"""
관리자 사이트 "최신화" 버튼용 - 온통청년/복지로(지자체)/복지로(중앙부처) 외부 데이터 수집
스크립트들을 백그라운드에서 실행하고 진행 상태를 메모리에 보관한다.

실행 스크립트(전부 bene_backend 루트에 있는 기존 스크립트를 그대로 서브프로세스로 호출),
독립적인 파이프라인(체인) 3개로 나뉜다 - 한 체인이 실패해도 다른 체인은 계속 진행된다:

    [온통청년]
        1. import_policies.py          (독립 실행. zipCd -> policy_region 매핑도 여기서 같이 함)

    [복지로 - 지자체]
        2. WELFARE.py                  (목록 재수집 -> welfare_data.json)
        3. fetch_welfare_detail.py     (상세조회 - 이미 받은 servId는 건너뛰고 신규분만 처리)
        4. import_welfare_policies.py  (온통청년 컬럼 매핑 후 DB 반영, policy_region 포함)

    [복지로 - 중앙부처]
        5. WELFARE2.py                          (목록 재수집 -> National_welfare_data.json)
        6. fetch_national_welfare_detail.py     (상세조회 - 신규분만 처리)
        7. import_national_welfare_policies.py  (온통청년 컬럼 매핑 후 DB 반영, policy_region 포함)

    (각 체인 내부는 순서대로 실행하고, 앞 단계가 실패하면 그 체인의 뒷 단계만 건너뜀.
    체인끼리는 서로 독립적이라 한 체인이 실패해도 다음 체인은 그대로 실행된다.)

위 3개 체인이 끝나면(일부 체인이 실패했더라도) policy/policy_region까지는 최신 상태이므로,
이어서 bene_ai에 "새로 추가된 정책만" summary/검색문서를 만들어달라고 트리거한다. 이 2단계는
로컬 서브프로세스가 아니라 bene_ai API를 호출 + 폴링하는 방식이라(AI_REBUILD_STEPS) 위
STEPS/_run_script와는 실행 방식이 다르지만, 진행 상태 표시(steps 리스트)에는 동일하게 얹는다.

상태는 서버 프로세스 메모리에만 저장한다(재시작하면 초기화). 여러 명이 동시에 누르는 걸
막기 위해 이미 실행 중이면 새 요청은 무시한다.
"""

import asyncio
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

from app.services.ai_client import AiClient

# 각 스크립트가 작업량을 알게 되는 시점에 찍는 마커 한 줄 (예: "TOTAL_COUNT:1191"). 관리자가
# 진행 중인 단계가 대략 얼마나 걸릴지 가늠할 수 있도록, 실시간 stdout에서 이 줄만 파싱해
# step["total"]에 채운다. 스크립트 쪽 print 위치는 각 파일에서 TOTAL_COUNT로 검색.
_TOTAL_COUNT_RE = re.compile(r"^TOTAL_COUNT:(\d+)$")

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

STEPS = [
    {"key": "ontong", "chain": "ontong", "label": "온통청년 공고문 갱신", "script": "import_policies.py", "timeout": 900},
    {"key": "bokjiro_list", "chain": "bokjiro_local", "label": "복지로(지자체) 목록 수집", "script": "WELFARE.py", "timeout": 300},
    {"key": "bokjiro_detail", "chain": "bokjiro_local", "label": "복지로(지자체) 상세조회", "script": "fetch_welfare_detail.py", "timeout": 1800},
    {"key": "bokjiro_import", "chain": "bokjiro_local", "label": "복지로(지자체) DB 반영", "script": "import_welfare_policies.py", "timeout": 600},
    {"key": "national_list", "chain": "bokjiro_national", "label": "복지로(중앙부처) 목록 수집", "script": "WELFARE2.py", "timeout": 300},
    {"key": "national_detail", "chain": "bokjiro_national", "label": "복지로(중앙부처) 상세조회", "script": "fetch_national_welfare_detail.py", "timeout": 1800},
    {"key": "national_import", "chain": "bokjiro_national", "label": "복지로(중앙부처) DB 반영", "script": "import_national_welfare_policies.py", "timeout": 600},
]

# policy/policy_region 동기화가 끝난 뒤 실행하는 후처리 단계 (bene_ai API 트리거 + 폴링).
AI_REBUILD_STEPS = [
    {
        "key": "policy_summary_rebuild",
        "label": "정책 요약(summary) 생성",
        "trigger": AiClient.trigger_policy_summary_rebuild,
        "status": AiClient.get_policy_summary_rebuild_status,
    },
    {
        "key": "search_docs_rebuild",
        "label": "검색문서/임베딩 생성",
        "trigger": AiClient.trigger_search_docs_rebuild,
        "status": AiClient.get_search_docs_rebuild_status,
    },
    {
        "key": "pdf_cache_rebuild",
        "label": "공고문 매칭 캐시 갱신",
        "trigger": AiClient.trigger_pdf_cache_rebuild,
        "status": AiClient.get_pdf_cache_rebuild_status,
    },
]

AI_REBUILD_POLL_SEC = 5
AI_REBUILD_MAX_WAIT_SEC = 3600

_OUTPUT_TAIL_CHARS = 4000

_status: dict = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "steps": [],
}


def get_status() -> dict:
    """최신화 작업의 현재 진행 상태(전체/단계별)를 반환한다."""
    return _status


def _init_steps() -> list[dict]:
    """이번 실행에서 거칠 모든 단계(스크립트 3체인 + AI 재구축 3개 + 캐시 반영 + 키워드 알림)를
    "pending" 상태로 초기화한다."""
    subprocess_steps = [
        {"key": s["key"], "label": s["label"], "status": "pending", "output": "", "total": None} for s in STEPS
    ]
    ai_steps = [
        {"key": s["key"], "label": s["label"], "status": "pending", "output": "", "total": None}
        for s in AI_REBUILD_STEPS
    ]
    policy_cache_step = [
        {"key": "policy_cache_sync", "label": "bene_ai 정책 메모리 캐시 반영", "status": "pending", "output": "", "total": None}
    ]
    keyword_alert_step = [
        {"key": "keyword_alert_check", "label": "알림 키워드 매칭 체크", "status": "pending", "output": "", "total": None}
    ]
    return subprocess_steps + ai_steps + policy_cache_step + keyword_alert_step


def _steps_by_chain() -> dict:
    """STEPS를 chain(온통청년/복지로-지자체/복지로-중앙부처)별로 묶는다."""
    chains: dict[str, list[dict]] = {}
    for s in STEPS:
        chains.setdefault(s["chain"], []).append(s)
    return chains


def _stream_pipe_lines(pipe, line_queue: "queue.Queue[str | None]") -> None:
    """별도 스레드에서 자식 프로세스의 stdout을 한 줄씩 읽어 큐에 넣는다. EOF에서 None을 넣어
    읽는 쪽이 프로세스 종료를 알 수 있게 한다."""
    try:
        for line in iter(pipe.readline, ""):
            line_queue.put(line)
    finally:
        line_queue.put(None)


def _run_script_blocking(script: str, timeout: int, step: dict) -> tuple[bool, str]:
    """
    asyncio.create_subprocess_exec는 Windows에서 uvicorn이 기본으로 쓰는
    이벤트 루프(SelectorEventLoop)와 맞지 않아 NotImplementedError를 던진다
    (asyncio 서브프로세스는 ProactorEventLoop가 필요함). 리눅스/윈도우 어디서든
    안전하게 동작하도록 Popen을 스레드에서 돌리는 방식으로 우회한다.

    subprocess.run(timeout=...)과 달리 stdout을 끝까지 기다리지 않고 한 줄씩 실시간으로
    읽는다 - TOTAL_COUNT: 마커가 보이는 즉시 step["total"]을 채워서, 관리자가 이 단계가
    끝나길 기다리는 동안 대략적인 작업량을 볼 수 있게 한다. 출력 자체는 계속 모아뒀다가
    끝나면 마지막 _OUTPUT_TAIL_CHARS만 반환한다(기존 동작과 동일).
    타임아웃은 큐에서 읽어올 때마다(최대 1초 간격) 남은 시간을 확인해서, 자식 프로세스가
    아무 출력도 안 하고 멈춰있는 경우에도 정확히 걸리도록 한다.
    """
    proc = None
    output_lines: list[str] = []
    try:
        proc = subprocess.Popen(
            # -u: 자식 프로세스가 파이프로 리다이렉트되면 파이썬 기본값이 블록 버퍼링이라
            # TOTAL_COUNT: 같은 초반 출력이 한참 안 나오고 버퍼에 갇힐 수 있다. 언버퍼드로
            # 강제해서 print()마다 바로 흘러나오게 한다.
            [sys.executable, "-u", script],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        line_queue: "queue.Queue[str | None]" = queue.Queue()
        reader = threading.Thread(target=_stream_pipe_lines, args=(proc.stdout, line_queue), daemon=True)
        reader.start()

        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                proc.kill()
                proc.wait()
                partial = "".join(output_lines)
                return False, f"{script} 실행이 {timeout}초를 넘겨 중단했습니다.\n{partial[-_OUTPUT_TAIL_CHARS:]}"
            try:
                line = line_queue.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                continue
            if line is None:  # EOF
                break
            output_lines.append(line)
            match = _TOTAL_COUNT_RE.match(line.strip())
            if match:
                step["total"] = int(match.group(1))

        returncode = proc.wait(timeout=max(0.1, deadline - time.monotonic()))
        text = "".join(output_lines)
        return returncode == 0, text[-_OUTPUT_TAIL_CHARS:]
    except subprocess.TimeoutExpired:
        if proc:
            proc.kill()
        partial = "".join(output_lines)
        return False, f"{script} 실행이 {timeout}초를 넘겨 중단했습니다.\n{partial[-_OUTPUT_TAIL_CHARS:]}"
    except OSError as e:
        return False, f"{script} 실행 실패: {e}"


async def _run_script(script: str, timeout: int, step: dict) -> tuple[bool, str]:
    """_run_script_blocking을 별도 스레드에서 돌려서 asyncio 이벤트 루프를 막지 않게 한다."""
    return await asyncio.to_thread(_run_script_blocking, script, timeout, step)


def _error_detail(e: Exception) -> str:
    """FastAPI HTTPException이면 detail을, 아니면 예외 메시지를 그대로 문자열로 꺼낸다."""
    return str(getattr(e, "detail", None) or e)


async def _run_ai_rebuild(trigger_fn, status_fn, step: dict) -> tuple[bool, str]:
    """bene_ai의 /rebuild 엔드포인트를 트리거하고, 끝날 때까지 폴링한다.
    trigger_fn/status_fn은 AiClient의 정적 메서드(각각 POST .../rebuild, GET .../rebuild/status)."""
    try:
        started = await trigger_fn()
    except Exception as e:
        return False, f"bene_ai 트리거 실패: {_error_detail(e)}"

    # 트리거 응답에 이미 new_count(작업량)가 실려오므로, 서브프로세스 단계의 TOTAL_COUNT와
    # 동일하게 시작하자마자 바로 채워준다.
    if isinstance(started.get("new_count"), int):
        step["total"] = started["new_count"]

    if started.get("status") == "up_to_date":
        return True, "신규 정책 없음 (건너뜀)"
    if started.get("status") not in ("started", "already_running"):
        return False, f"예상하지 못한 응답: {started}"

    waited = 0
    while waited < AI_REBUILD_MAX_WAIT_SEC:
        await asyncio.sleep(AI_REBUILD_POLL_SEC)
        waited += AI_REBUILD_POLL_SEC
        try:
            status = await status_fn()
        except Exception as e:
            return False, f"bene_ai 상태 조회 실패: {_error_detail(e)}"

        if not status.get("running"):
            last_run = status.get("last_run") or {}
            if last_run.get("error"):
                return False, f"오류: {last_run['error']}"
            # 3개 rebuild 엔드포인트가 last_run에 담는 필드가 서로 달라서(예: policy_summary_rebuild는
            # requested/processed/failed, pdf_cache_rebuild는 policy_count) 필드명을 하드코딩하지 않고
            # 있는 값을 그대로 나열한다.
            details = ", ".join(f"{k}={v}" for k, v in last_run.items() if k != "error" and v is not None)
            return True, details or "완료"

    return False, f"{AI_REBUILD_MAX_WAIT_SEC}초 내에 끝나지 않았습니다."


async def run_refresh_all():
    """관리자 "최신화" 버튼의 진입점. 3개 수집 체인을 순서대로 실행하고, 이어서 bene_ai
    재구축(요약/검색문서/PDF캐시), 정책 메모리 캐시 반영, 알림 키워드 매칭까지 전부 수행한다.
    이미 실행 중이면 아무것도 하지 않는다(중복 실행 방지)."""
    if _status["running"]:
        return

    started_at_dt = datetime.now()
    _status["running"] = True
    _status["started_at"] = started_at_dt.isoformat()
    _status["finished_at"] = None
    _status["steps"] = _init_steps()

    try:
        for chain_steps in _steps_by_chain().values():
            chain_failed = False
            for s in chain_steps:
                step = next(st for st in _status["steps"] if st["key"] == s["key"])
                if chain_failed:
                    step["status"] = "skipped"
                    continue
                step["status"] = "running"
                try:
                    ok, out = await _run_script(s["script"], s["timeout"], step)
                except Exception as e:
                    ok, out = False, f"예상하지 못한 오류: {e}"
                step["status"] = "success" if ok else "failed"
                step["output"] = out
                if not ok:
                    chain_failed = True

        # 위 체인들이 일부 실패했더라도 policy/policy_region은 최신 상태이므로,
        # 새로 추가된 정책의 summary/검색문서 생성은 항상 시도한다(best-effort).
        for s in AI_REBUILD_STEPS:
            step = next(st for st in _status["steps"] if st["key"] == s["key"])
            step["status"] = "running"
            try:
                ok, out = await _run_ai_rebuild(s["trigger"], s["status"], step)
            except Exception as e:
                ok, out = False, f"예상하지 못한 오류: {e}"
            step["status"] = "success" if ok else "failed"
            step["output"] = out

        # bene_ai의 PolicyLoaderService는 서버 시작 시 DB를 한 번만 읽어 메모리에 캐싱하고
        # 그 뒤로는 다시 안 읽는다. raw SQL 배치로 들어온 신규/변경 정책은 bene_ai를 재시작하기
        # 전까지 추천/알림 매칭에서 영원히 안 보이므로, started_at_dt 이후 신규/변경된 정책들을
        # 여기서 bene_ai 메모리 캐시에 밀어넣어준다(아래 키워드 매칭 체크보다 먼저 실행되어야 함).
        cache_step = next(st for st in _status["steps"] if st["key"] == "policy_cache_sync")
        cache_step["status"] = "running"
        try:
            from app.db.database import AsyncSessionLocal
            from app.db.crud.policy import PolicyCrud
            from app.services.policy import PolicyService
            from app.services.ai_client import AiClient

            async with AsyncSessionLocal() as session:
                changed_policies = await PolicyCrud.get_changed_since(session, started_at_dt)
                synced, failed = 0, 0
                for policy in changed_policies:
                    try:
                        payload = PolicyService._build_policy_cache_payload(policy)
                        await AiClient.sync_policy_cache_upsert(payload)
                        synced += 1
                    except Exception:
                        failed += 1
            cache_step["status"] = "success" if failed == 0 else "failed"
            cache_step["output"] = f"{synced}/{len(changed_policies)}건 반영" + (f" ({failed}건 실패)" if failed else "")
        except Exception as e:
            cache_step["status"] = "failed"
            cache_step["output"] = f"정책 캐시 반영 실패: {e}"

        # 온통청년/복지로 raw SQL 배치는 ORM을 거치지 않아 create/update 훅을 못 타므로,
        # 여기서 started_at_dt 이후 신규/변경된 정책만 모아 알림 키워드 매칭을 한 번에 체크한다.
        keyword_step = next(st for st in _status["steps"] if st["key"] == "keyword_alert_check")
        keyword_step["status"] = "running"
        try:
            from app.db.database import AsyncSessionLocal
            from app.services.user_alert_keyword import UserAlertKeywordService

            async with AsyncSessionLocal() as session:
                created = await UserAlertKeywordService.check_and_notify_since_svc(session, started_at_dt)
            keyword_step["status"] = "success"
            keyword_step["output"] = f"알림 {created}건 생성"
        except Exception as e:
            keyword_step["status"] = "failed"
            keyword_step["output"] = f"키워드 알림 체크 실패: {e}"
    finally:
        _status["running"] = False
        _status["finished_at"] = datetime.now().isoformat()
