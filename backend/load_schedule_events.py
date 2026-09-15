"""
1) 온통청년 API 원본 JSON에서 srngMthdCn(심사방법)을 읽어 policy 테이블을 백필하고,
2) AI(watsonx) 일정 추출 캐시(ai_schedule_cache.json)를 policy_schedule_event 테이블에 적재하는 스크립트.

캐시는 plcyNo를 키로 하는 { plcyNo: [{type, date, raw_text}, ...] } 형태
(C:\\OPEN-API\\Calendar_Test 의 rule-engine + watsonx 스크립트가 미리 만들어둔 결과물).
watsonx 키 없이도 실행 가능 (파일 기반 로딩만 함).

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 policy 적재 때 쓰던 것 그대로 사용)

사용법:
    python load_schedule_events.py
    python load_schedule_events.py --raw-json "다른경로.json" --cache "다른캐시.json"
"""

import os
import sys
import json
import argparse
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
}

DEFAULT_RAW_JSON = Path(r"C:\OPEN-API\성능평가\ontongAPI_2632.json")
DEFAULT_CACHE_JSON = Path(r"C:\OPEN-API\Calendar_Test\ai_schedule_cache.json")


def find_record_list(data):
    """원본 JSON이 어떤 형태로 저장돼있든 plcyNo를 가진 dict의 리스트를 찾아서 반환."""
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "plcyNo" in data[0]:
            return data
        for item in data:
            found = find_record_list(item)
            if found:
                return found
        return None

    if isinstance(data, dict):
        for value in data.values():
            found = find_record_list(value)
            if found:
                return found

    return None


def build_plcyno_to_id_map(conn) -> dict:
    """전체 정책의 plcyNo -> policy_id 매핑을 만든다."""
    with conn.cursor() as cur:
        cur.execute("SELECT policy_id, plcyNo FROM policy")
        rows = cur.fetchall()
    return {plcy_no: policy_id for policy_id, plcy_no in rows}


def ensure_srng_mthd_column(conn) -> None:
    """Base.metadata.create_all은 기존 테이블에 새 컬럼을 추가해주지 않으므로 직접 확인 후 추가."""
    with conn.cursor() as cur:
        cur.execute("SHOW COLUMNS FROM policy LIKE 'srngMthdCn'")
        if cur.fetchone() is None:
            print("  policy.srngMthdCn 컬럼이 없어 추가합니다...")
            cur.execute("ALTER TABLE policy ADD COLUMN srngMthdCn TEXT")
    conn.commit()


def backfill_srng_mthd(conn, raw_json_path: Path, plcyno_map: dict) -> int:
    """원본 API JSON에서 심사방법(srngMthdCn)을 읽어 policy 테이블에 채운다."""
    print(f"[1/2] {raw_json_path.name} 에서 srngMthdCn 백필 중...")
    ensure_srng_mthd_column(conn)
    with open(raw_json_path, encoding="utf-8") as f:
        raw = json.load(f)
    records = find_record_list(raw)
    if not records:
        print("  [경고] plcyNo를 가진 레코드 리스트를 못 찾음. 백필 스킵.")
        return 0

    pairs = []
    for rec in records:
        plcy_no = rec.get("plcyNo")
        srng = rec.get("srngMthdCn")
        policy_id = plcyno_map.get(plcy_no)
        if policy_id is None or not srng:
            continue
        pairs.append((srng, policy_id))

    if not pairs:
        print("  업데이트할 srngMthdCn 없음.")
        return 0

    sql = "UPDATE policy SET srngMthdCn = %s WHERE policy_id = %s"
    with conn.cursor() as cur:
        cur.executemany(sql, pairs)
    conn.commit()
    print(f"  {len(pairs)}건 업데이트 완료.")
    return len(pairs)


def load_events(conn, cache_path: Path, plcyno_map: dict) -> int:
    """AI가 미리 추출해둔 일정 캐시(plcyNo -> 일정 목록)를 policy_schedule_event 테이블에 적재한다."""
    print(f"[2/2] {cache_path.name} 에서 일정 캐시 적재 중...")
    with open(cache_path, encoding="utf-8") as f:
        cache = json.load(f)

    rows = []
    missing_policy = 0
    for plcy_no, events in cache.items():
        if not events or isinstance(events, dict):  # {"error": "..."} 형태는 스킵
            continue
        policy_id = plcyno_map.get(plcy_no)
        if policy_id is None:
            missing_policy += 1
            continue
        for e in events:
            rows.append((policy_id, e.get("type", ""), e.get("date", ""), e.get("raw_text", "")))

    if missing_policy:
        print(f"  [경고] policy 테이블에서 plcyNo를 못 찾아 스킵한 정책: {missing_policy}건")

    if not rows:
        print("  적재할 일정 없음.")
        return 0

    sql = (
        "INSERT IGNORE INTO policy_schedule_event (policy_id, event_type, event_date, raw_text) "
        "VALUES (%s, %s, %s, %s)"
    )
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    print(f"  {len(rows)}건 적재 시도 완료 (중복은 INSERT IGNORE로 자동 스킵).")
    return len(rows)


def main():
    """심사방법 백필과 일정 캐시 적재를 순서대로 실행한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-json", default=str(DEFAULT_RAW_JSON), help="온통청년 원본 API 응답 JSON 경로")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE_JSON), help="AI 일정 추출 캐시 JSON 경로")
    args = parser.parse_args()

    raw_json_path = Path(args.raw_json)
    cache_path = Path(args.cache)

    if not raw_json_path.exists():
        sys.exit(f"원본 JSON 경로가 존재하지 않습니다: {raw_json_path}")
    if not cache_path.exists():
        sys.exit(f"캐시 JSON 경로가 존재하지 않습니다: {cache_path}")

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        plcyno_map = build_plcyno_to_id_map(conn)
        print(f"매핑된 policy 건수: {len(plcyno_map)}")

        backfill_srng_mthd(conn, raw_json_path, plcyno_map)
        load_events(conn, cache_path, plcyno_map)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
