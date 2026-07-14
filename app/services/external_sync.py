"""
관리자 사이트 "최신화" 버튼용 - 온통청년/복지로(지자체)/복지로(중앙부처) 외부 데이터 수집
스크립트들을 백그라운드에서 실행하고 진행 상태를 메모리에 보관한다.

실행 스크립트(전부 bene_backend 루트에 있는 기존 스크립트를 그대로 서브프로세스로 호출),
독립적인 파이프라인(체인) 3개로 나뉜다 - 한 체인이 실패해도 다른 체인은 계속 진행된다:

    [온통청년]
        1. import_policies.py          (독립 실행)

    [복지로 - 지자체]
        2. WELFARE.py                  (목록 재수집 -> welfare_data.json)
        3. fetch_welfare_detail.py     (상세조회 - 이미 받은 servId는 건너뛰고 신규분만 처리)
        4. import_welfare_policies.py  (온통청년 컬럼 매핑 후 DB 반영)

    [복지로 - 중앙부처]
        5. WELFARE2.py                          (목록 재수집 -> National_welfare_data.json)
        6. fetch_national_welfare_detail.py     (상세조회 - 신규분만 처리)
        7. import_national_welfare_policies.py  (온통청년 컬럼 매핑 후 DB 반영)

    (각 체인 내부는 순서대로 실행하고, 앞 단계가 실패하면 그 체인의 뒷 단계만 건너뜀.
    체인끼리는 서로 독립적이라 한 체인이 실패해도 다음 체인은 그대로 실행된다.)

상태는 서버 프로세스 메모리에만 저장한다(재시작하면 초기화). 여러 명이 동시에 누르는 걸
막기 위해 이미 실행 중이면 새 요청은 무시한다.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

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

_OUTPUT_TAIL_CHARS = 4000

_status: dict = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "steps": [],
}


def get_status() -> dict:
    return _status


def _init_steps() -> list[dict]:
    return [{"key": s["key"], "label": s["label"], "status": "pending", "output": ""} for s in STEPS]


def _steps_by_chain() -> dict:
    chains: dict[str, list[dict]] = {}
    for s in STEPS:
        chains.setdefault(s["chain"], []).append(s)
    return chains


async def _run_script(script: str, timeout: int) -> tuple[bool, str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, script,
            cwd=str(BACKEND_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as e:
        return False, f"{script} 실행 실패: {e}"

    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return False, f"{script} 실행이 {timeout}초를 넘겨 중단했습니다."

    text = out.decode("utf-8", errors="replace")
    return proc.returncode == 0, text[-_OUTPUT_TAIL_CHARS:]


async def run_refresh_all():
    if _status["running"]:
        return

    _status["running"] = True
    _status["started_at"] = datetime.now().isoformat()
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
                ok, out = await _run_script(s["script"], s["timeout"])
                step["status"] = "success" if ok else "failed"
                step["output"] = out
                if not ok:
                    chain_failed = True
    finally:
        _status["running"] = False
        _status["finished_at"] = datetime.now().isoformat()
