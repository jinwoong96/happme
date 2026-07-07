"""
서울시 공공서비스예약(구별 x 카테고리별) JSON 파일들을 local_program 테이블에 적재하는 스크립트

폴더 구조 예시 (재귀로 전부 훑음):
    backend/
      서울시 동대문구/
        서울시 동대문구 교육 공공서비스예약 정보.json
        서울시 동대문구 문화행사 공공서비스예약 정보.json
        ...
      서울시 서대문구/
        ...

각 JSON 파일은 {"DESCRIPTION": {...}, "DATA": [ {...}, ... ]} 구조.

사전 준비:
    pip install pymysql python-dotenv
    (RDS 접속 정보는 policy 적재 때 쓰던 .env 그대로 사용)

사용법:
    python load_local_programs.py --root "./backend"
"""

import os
import sys
import json
import argparse
from datetime import datetime
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

# DB 컬럼명 : JSON DATA 안의 키 (동일하지만 좌표만 이름이 바뀜)
FIELD_MAP = {
    "svcid": "svcid",
    "svcnm": "svcnm",
    "svcstatnm": "svcstatnm",
    "usetgtinfo": "usetgtinfo",
    "gubun": "gubun",
    "minclassnm": "minclassnm",
    "maxclassnm": "maxclassnm",
    "payatnm": "payatnm",
    "svcurl": "svcurl",
    "placenm": "placenm",
    "areanm": "areanm",
    "rcptbgndt": "rcptbgndt",
    "rcptenddt": "rcptenddt",
    "svcopnbgndt": "svcopnbgndt",
    "svcopnenddt": "svcopnenddt",
    "latitude": "y",
    "longitude": "x",
}

COLUMNS = list(FIELD_MAP.keys())

EPOCH_MS_FIELDS = {"rcptbgndt", "rcptenddt", "svcopnbgndt", "svcopnenddt"}

# 청년 혜택 서비스이므로 아래 대상만 콕 집은(=성인이 함께 명시되지 않은) 서비스는 제외한다.
EXCLUDE_KEYWORDS = ["유아","어린이", "초등학생", "중학생", "고등학생", "노인", "어르신", "중장년층"]
KEEP_KEYWORD = "성인"


def is_excluded_target(usetgtinfo: str) -> bool:
    if not usetgtinfo:
        return False
    return any(kw in usetgtinfo for kw in EXCLUDE_KEYWORDS) and KEEP_KEYWORD not in usetgtinfo


def parse_epoch_ms(value):
    if value in (None, "", 0):
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000)
    except (ValueError, TypeError, OSError):
        return None


def parse_decimal(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def row_from_item(item: dict) -> tuple:
    row = []
    for col in COLUMNS:
        src_key = FIELD_MAP[col]
        val = item.get(src_key)

        if col in EPOCH_MS_FIELDS:
            val = parse_epoch_ms(val)
        elif col in ("latitude", "longitude"):
            val = parse_decimal(val)
        elif isinstance(val, str):
            val = val.strip()
            if val == "":
                val = None

        row.append(val)
    return tuple(row)


def load_json_files(root: Path):
    files = sorted(root.rglob("*.json"))
    if not files:
        sys.exit(f"'{root}' 아래에서 .json 파일을 찾지 못했습니다.")
    return files


def cleanup_excluded(conn) -> int:
    """이미 local_program에 들어가있는 행 중 제외 대상(EXCLUDE_KEYWORDS)인 것들을 삭제."""
    with conn.cursor() as cur:
        cur.execute("SELECT svcid, usetgtinfo FROM local_program")
        rows = cur.fetchall()

    svcids_to_delete = [svcid for svcid, usetgtinfo in rows if is_excluded_target(usetgtinfo)]
    if not svcids_to_delete:
        return 0

    with conn.cursor() as cur:
        placeholders = ", ".join(["%s"] * len(svcids_to_delete))
        cur.execute(f"DELETE FROM local_program WHERE svcid IN ({placeholders})", svcids_to_delete)
    conn.commit()
    return len(svcids_to_delete)


def insert_batch(conn, rows: list):
    if not rows:
        return 0

    col_list = ", ".join(f"`{c}`" for c in COLUMNS)
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    update_clause = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in COLUMNS if c != "svcid")

    sql = f"""
        INSERT INTO local_program ({col_list})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
    """

    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="JSON 파일들이 들어있는 최상위 폴더 (예: ./backend)")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        sys.exit(f"경로가 존재하지 않습니다: {root}")

    files = load_json_files(root)
    print(f"발견된 JSON 파일 수: {len(files)}")

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    total = 0
    total_skipped = 0
    try:
        deleted = cleanup_excluded(conn)
        print(f"기존 local_program에서 제외 대상(유아/어린이/초등학생/중학생/고등학생/노인/어르신/중장년층, "
              f"단 '성인' 병기된 경우는 제외 안 함) {deleted}건 삭제")

        for fp in files:
            with open(fp, encoding="utf-8") as f:
                try:
                    raw = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"  [스킵] {fp.name}: JSON 파싱 실패 ({e})")
                    continue

            items = raw.get("DATA", [])
            if not items:
                print(f"  [스킵] {fp.name}: DATA 없음")
                continue

            kept_items = [item for item in items if not is_excluded_target(item.get("usetgtinfo"))]
            skipped = len(items) - len(kept_items)
            total_skipped += skipped

            rows = [row_from_item(item) for item in kept_items]
            inserted = insert_batch(conn, rows)
            total += inserted
            print(f"  [{fp.parent.name}] {fp.name}: {inserted}건 적재 (제외 {skipped}건)")

    finally:
        conn.close()

    print(f"완료. 총 {total}건 적재/업데이트, 신규 적재 시 제외 {total_skipped}건, 기존 데이터 삭제 {deleted}건.")


if __name__ == "__main__":
    main()