"""
[임시/테스트 전용] PolicyEligibilityEngine의 match 함수(_match_age, region_matcher.match 등)별
실행시간을 재는 디버그 유틸리티. rule_engine_cache 캐시 미스 시 왜 오래 걸리는지(어느 체크
함수가 병목인지) 보려고 만든 것으로, 프로젝트에 영구로 남길 목적이 아니다.

RULE_ENGINE_TIMING_DEBUG=1 환경변수가 설정된 경우에만 활성화된다. 꺼져 있으면(기본값)
@timed 데코레이터가 원본 함수를 그대로 반환하므로 평소 운영에는 오버헤드가 전혀 없다.

테스트가 끝나면 이 파일을 지우고, eligibility_rules.py / region_matcher.py에 추가한
"from app.core.match_timing_debug import timed" import 한 줄과 각 함수 위 "@timed(...)"
데코레이터 줄만 제거하면 완전히 원상복구된다.

사용법:
    RULE_ENGINE_TIMING_DEBUG=1 uvicorn main:app --reload --port=8090
    (평소처럼 /recommendations/ 등을 호출하면 자동으로 누적됨)

    통계는 FLUSH_EVERY(기본 2000)회 호출마다 자동으로 logs/match_timing_debug.json에 저장된다.
    uvicorn --reload가 워커를 강제 종료하는 경우가 흔해(특히 Windows) 정상 종료 훅(atexit)에만
    기대면 데이터가 유실될 수 있어서, 종료를 기다리지 않고 실행 중에 주기적으로 파일에 쓴다.
    atexit도 백업으로 등록해두지만, 신뢰할 건 주기적 flush 쪽이다.

    언제든 강제로 지금 상태를 저장하고 싶으면:
    python -c "from app.core.match_timing_debug import dump_timing_stats; print(dump_timing_stats())"
    (단, 이건 이 파이썬 프로세스 자체의 메모리만 볼 수 있어 실행 중인 서버 프로세스에는 못 쓴다 -
    서버가 이미 주기적으로 자동 저장하므로 그냥 logs/match_timing_debug.json을 직접 읽으면 된다.)
"""

import atexit
import functools
import json
import os
import time
from collections import defaultdict

TIMING_ENABLED = os.getenv("RULE_ENGINE_TIMING_DEBUG") == "1"
FLUSH_EVERY = int(os.getenv("RULE_ENGINE_TIMING_DEBUG_FLUSH_EVERY", "2000"))

_stats: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "total_ms": 0.0})
_DUMP_PATH = os.getenv("RULE_ENGINE_TIMING_DEBUG_PATH", os.path.join("logs", "match_timing_debug.json"))
_calls_since_flush = 0


def timed(name: str):
    """RULE_ENGINE_TIMING_DEBUG=1일 때만 감싸고, 꺼져 있으면 원본 함수를 그대로 반환한다
    (제로 오버헤드). 인메모리로 누적하면서 FLUSH_EVERY 호출마다 파일에도 자동으로 써서,
    프로세스가 강제 종료돼도(atexit이 안 돌아도) 마지막 flush 시점까지는 데이터가 남는다."""
    def decorator(func):
        if not TIMING_ENABLED:
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global _calls_since_flush
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                stat = _stats[name]
                stat["count"] += 1
                stat["total_ms"] += elapsed_ms
                _calls_since_flush += 1
                if _calls_since_flush >= FLUSH_EVERY:
                    _calls_since_flush = 0
                    dump_timing_stats()
        return wrapper
    return decorator


def dump_timing_stats(path: str | None = None) -> dict:
    """지금까지 누적된 함수별 {count, total_ms, avg_ms}를 JSON으로 저장하고 반환한다."""
    result = {
        name: {
            "count": int(s["count"]),
            "total_ms": round(s["total_ms"], 2),
            "avg_ms": round(s["total_ms"] / s["count"], 4) if s["count"] else 0.0,
        }
        for name, s in sorted(_stats.items(), key=lambda kv: -kv[1]["total_ms"])
    }
    out_path = path or _DUMP_PATH
    dirname = os.path.dirname(out_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


if TIMING_ENABLED:
    atexit.register(dump_timing_stats)  # 정상 종료 시엔 이것도 최종 저장을 한번 더 해준다(백업)
