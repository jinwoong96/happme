"""
온통청년 Open API 공고문 데이터를 MySQL policy 테이블에 적재하는 스크립트

사전 준비:
    pip install requests pymysql python-dotenv

사용법:
    1. .env.example 을 .env 로 복사하고 실제 값 채우기
    2. python import_policies.py --peek   # API 응답 구조 먼저 확인 (1건만 조회)
    3. python import_policies.py          # 전체 적재 실행
"""

import os
import sys
import time
import argparse
from datetime import datetime

import requests
import pymysql
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
API_KEY = os.getenv("ONTONG_API_KEY")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
}

PAGE_SIZE = 100  # 온통청년 API 한 페이지 최대 요청 건수 (환경에 따라 조정 필요할 수 있음)

# policy 테이블 컬럼 순서 (auto_increment인 policy_id, createdAt/updatedAt DEFAULT 제외)
COLUMNS = [
    "plcyNo", "plcyNm", "plcyKywdNm", "plcyExplnCn", "lclsfNm", "mclsfNm",
    "plcySprtCn", "sprvsnInstCdNm", "sprvsnInstPicNm", "operInstCdNm", "operInstPicNm",
    "bizPrdBgngYmd", "bizPrdEndYmd", "bizPrdEtcCn", "plcyAplyMthdCn", "aplyUrlAddr",
    "sbmsnDcmntCn", "aplyYmd", "refUrlAddr1", "refUrlAddr2", "etcMttrCn",
    "sprtSclCnt", "sprtTrgtMinAge", "sprtTrgtMaxAge", "earnMinAmt", "earnMaxAmt",
    "earnEtcCn", "earnCndSeCd", "addAplyQlfcCndCn", "ptcpPrpTrgtCn", "mrgSttsCd",
    "inqCnt", "frstRegDt", "lastMdfcnDt",
]

# NOT NULL인데 API에서 비어있을 수 있는 컬럼들의 기본값 처리용
NOT_NULL_TEXT_DEFAULTS = {
    "plcyNm", "plcyKywdNm", "plcyExplnCn", "lclsfNm", "mclsfNm", "plcySprtCn",
    "sbmsnDcmntCn", "aplyYmd", "earnEtcCn", "addAplyQlfcCndCn", "ptcpPrpTrgtCn",
}


def parse_int(value):
    if value in (None, "", "null"):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_datetime(value):
    """온통청년 API는 보통 'yyyyMMddHHmmss' 또는 'yyyy-MM-dd HH:mm:ss' 형태로 옴"""
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def fetch_page(page_num: int) -> dict:
    params = {
        "apiKeyNm": API_KEY,
        "pageNum": page_num,
        "pageSize": PAGE_SIZE,
        "rtnType": "json",
    }
    resp = requests.get(API_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def extract_items(raw: dict) -> list:
    """
    응답 구조가 문서/버전에 따라 다를 수 있어 방어적으로 파싱.
    일반적으로 raw["result"]["youthPolicyList"] 형태.
    """
    try:
        return raw["result"]["youthPolicyList"]
    except (KeyError, TypeError):
        pass

    # 혹시 다른 키 이름을 쓰는 경우를 대비한 폴백: list인 값을 가진 첫 키를 찾음
    def find_list(d):
        if isinstance(d, dict):
            for v in d.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    return v
                found = find_list(v)
                if found:
                    return found
        return None

    items = find_list(raw)
    if items is None:
        raise ValueError(
            "응답에서 공고 리스트를 찾지 못했습니다. --peek 옵션으로 원본 구조를 확인하세요."
        )
    return items


def get_total_count(raw: dict) -> int:
    try:
        return int(raw["result"]["pagging"]["totCount"])
    except (KeyError, TypeError, ValueError):
        return -1  # 알 수 없으면 -1, 빈 페이지 나올 때까지 반복


def row_from_item(item: dict) -> tuple:
    row = []
    for col in COLUMNS:
        val = item.get(col)

        if col in ("sprtSclCnt", "sprtTrgtMinAge", "sprtTrgtMaxAge",
                    "earnMinAmt", "earnMaxAmt", "inqCnt"):
            val = parse_int(val)
        elif col in ("frstRegDt", "lastMdfcnDt"):
            val = parse_datetime(val)
        else:
            if val is None:
                val = "" if col in NOT_NULL_TEXT_DEFAULTS else None
            elif isinstance(val, str):
                val = val.strip()

        row.append(val)
    return tuple(row)


def insert_batch(conn, rows: list):
    if not rows:
        return

    col_list = ", ".join(f"`{c}`" for c in COLUMNS)
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    update_clause = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in COLUMNS if c != "plcyNo")

    sql = f"""
        INSERT INTO policy ({col_list})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
    """

    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--peek", action="store_true", help="1페이지만 조회해서 원본 응답 구조 출력")
    args = parser.parse_args()

    if not API_KEY:
        sys.exit("ONTONG_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    if args.peek:
        raw = fetch_page(1)
        import json
        print(json.dumps(raw, ensure_ascii=False, indent=2)[:3000])
        return

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    page_num = 1
    total_inserted = 0
    total_count = None

    try:
        while True:
            raw = fetch_page(page_num)

            if total_count is None:
                total_count = get_total_count(raw)
                if total_count > 0:
                    print(f"전체 공고 건수: {total_count}")

            items = extract_items(raw)
            if not items:
                print("더 이상 데이터 없음. 종료.")
                break

            rows = [row_from_item(item) for item in items]
            insert_batch(conn, rows)
            total_inserted += len(rows)
            print(f"[page {page_num}] {len(rows)}건 처리 (누적 {total_inserted}건)")

            if total_count > 0 and total_inserted >= total_count:
                break
            if len(items) < PAGE_SIZE:
                break

            page_num += 1
            time.sleep(0.3)  # API 과호출 방지

    finally:
        conn.close()

    print(f"완료. 총 {total_inserted}건 적재/업데이트.")


if __name__ == "__main__":
    main()