"""
DB에서 summary가 비어있는 정책만 골라 policy.summary 컬럼을 채우는 백그라운드 파이프라인.

run_create_policy_summaries.py/policy_card_generator.py(WatsonxPolicySummaryGenerator)와 같은
프롬프트/모델을 재사용하되, data/policy_list.json과 result/*.json 파일을 거치지 않고
DB에서 바로 읽어 DB에 바로 쓴다. search_docs_builder.py와 동일한 구조(신규분만 감지 ->
배치 생성 -> 배치마다 즉시 반영 -> 상태 폴링)를 따른다.
"""

import threading
import time

import pymysql

from app.core.settings import settings
from policy_card_generator import WatsonxPolicySummaryGenerator, DEFAULT_LLM_INPUT_FIELDS

BATCH_SIZE = 5
SLEEP_SEC = 0.2

_lock = threading.Lock()
_status: dict = {"running": False, "last_run": None}


def get_status() -> dict:
    return {"running": _status["running"], "last_run": _status["last_run"]}


def _connect():
    return pymysql.connect(
        host=settings.db_host, port=settings.db_port, user=settings.db_user,
        password=settings.db_password, db=settings.db_name, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_new_policies() -> list[dict]:
    """summary가 비어있고 요약할 지원내용(plcySprtCn)이 있는 정책만 대상으로 한다."""
    conn = _connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {', '.join(DEFAULT_LLM_INPUT_FIELDS)} FROM policy
                WHERE (summary IS NULL OR summary = '') AND plcySprtCn != ''
                """
            )
            return cursor.fetchall()
    finally:
        conn.close()


def _update_summaries(pairs: list[tuple[str, str]]) -> None:
    """pairs: [(support_summary, plcyNo), ...]"""
    if not pairs:
        return
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.executemany("UPDATE policy SET summary = %s WHERE plcyNo = %s", pairs)
        conn.commit()
    finally:
        conn.close()


def run_rebuild(new_policies: list[dict]) -> None:
    """new_policies에 대해 support_summary를 생성해 policy.summary에 바로 반영한다.
    BATCH_SIZE만큼씩 나눠서 배치마다 DB에 바로 저장하므로, 중간에 실패/재시작해도
    그때까지 처리한 배치는 남아있다. BackgroundTasks에서 호출되는 동기 함수."""
    with _lock:
        if _status["running"]:
            return
        _status["running"] = True

    result = {"requested": len(new_policies), "processed": 0, "failed": 0, "error": None}
    _status["last_run"] = dict(result)
    try:
        if not new_policies:
            return

        generator = WatsonxPolicySummaryGenerator()

        total_batches = (len(new_policies) - 1) // BATCH_SIZE + 1
        for batch_idx, start in enumerate(range(0, len(new_policies), BATCH_SIZE), start=1):
            batch = new_policies[start:start + BATCH_SIZE]
            print(f"[policy_summary_builder] 배치 {batch_idx}/{total_batches} 생성 중...")

            pairs = []
            for policy in batch:
                plcy_no = policy.get("plcyNo")
                try:
                    summary_result = generator.summarize_one(policy)
                    support_summary = (summary_result.get("support_summary") or "").strip()
                    if support_summary and plcy_no:
                        pairs.append((support_summary, plcy_no))
                        result["processed"] += 1
                except Exception as e:
                    result["failed"] += 1
                    print(f"[policy_summary_builder] 실패: {policy.get('plcyNm')} / {e}")
                if SLEEP_SEC > 0:
                    time.sleep(SLEEP_SEC)

            _update_summaries(pairs)
            _status["last_run"] = dict(result)
    except Exception as e:
        result["error"] = str(e)
    finally:
        _status["running"] = False
        _status["last_run"] = result
