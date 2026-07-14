"""
관리자 사이트 "최신화" 버튼용 - 온통청년/복지로 외부 데이터 수집 스크립트들을
백그라운드에서 순서대로 실행하고 진행 상태를 메모리에 보관한다.

실행 스크립트(전부 bene_backend 루트에 있는 기존 스크립트를 그대로 서브프로세스로 호출):
    1. import_policies.py          (온통청년 - 독립적으로 실행, 실패해도 복지로는 계속 진행)
    2. WELFARE.py                  (복지로 목록 재수집 -> welfare_data.json)
    3. fetch_welfare_detail.py     (복지로 상세조회 - 이미 받은 servId는 건너뛰므로 매번 신규분만 처리됨)
    4. import_welfare_policies.py  (복지로 -> 온통청년 컬럼 매핑 후 DB 반영)
    (2~4는 순서대로 실행하고, 앞 단계가 실패하면 뒤 단계는 건너뜀)

상태는 서버 프로세스 메모리에만 저장한다(재시작하면 초기화). 여러 명이 동시에 누르는 걸
막기 위해 이미 실행 중이면 새 요청은 무시한다.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

STEPS = [
    {"key": "ontong", "label": "온통청년 공고문 갱신", "script": "import_policies.py", "timeout": 900},
    {"key": "bokjiro_list", "label": "복지로 목록 수집", "script": "WELFARE.py", "timeout": 300},
    {"key": "bokjiro_detail", "label": "복지로 상세조회", "script": "fetch_welfare_detail.py", "timeout": 1800},
    {"key": "bokjiro_import", "label": "복지로 DB 반영", "script": "import_welfare_policies.py", "timeout": 600},
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
        # 1) 온통청년 - 복지로 파이프라인과 독립적이므로 실패해도 아래는 계속 진행
        step = _status["steps"][0]
        step["status"] = "running"
        ok, out = await _run_script(STEPS[0]["script"], STEPS[0]["timeout"])
        step["status"] = "success" if ok else "failed"
        step["output"] = out

        # 2~4) 복지로 체인 - 앞 단계 실패하면 뒷 단계는 건너뜀
        chain_failed = False
        for s in STEPS[1:]:
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
