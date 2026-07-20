"""
온통청년 Open API 공고문 데이터를 MySQL policy 테이블에 적재하는 스크립트

사전 준비:
    pip install requests pymysql python-dotenv

사용법:
    1. .env.example 을 .env 로 복사하고 실제 값 채우기
    2. python import_policies.py --peek   # API 응답 구조 먼저 확인 (1건만 조회)
    3. python import_policies.py          # 전체 적재 실행

    새 컬럼을 모델에 추가한 뒤 기존 행에 값만 채워 넣고 싶을 때(전체 재적재로 인해
    관리자 화면에서 수동으로 고친 다른 필드값이 덮어써지는 걸 피하고 싶을 때):
    4. python import_policies.py --backfill-columns rgtrInstCdNm
       (plcyNo로 매칭해서 지정한 컬럼만 UPDATE. 쉼표로 여러 개 지정 가능)

    source 컬럼을 새로 추가한 뒤 기존 행 백필:
    5. DB에 컬럼이 없다면 먼저 수동으로 추가:
       ALTER TABLE policy ADD COLUMN source VARCHAR(20) NULL AFTER plcySprtCn;
    6. python import_policies.py --backfill-columns source
       (plcyNo가 있는 기존 온통청년 행들에 source='ONTONG' 채움)
    7. 수동추가 정책(plcyNo가 NULL이라 위 백필로는 안 채워짐)은 직접 실행:
       UPDATE policy SET source='MANUAL' WHERE plcyNo IS NULL AND source IS NULL;
"""

import os
import sys
import time
import argparse
from datetime import datetime

import requests
import pymysql
from dotenv import load_dotenv

from load_policy_regions import build_plcyno_to_id_map, build_region_pairs, insert_pairs

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
    "plcySprtCn", "source", "rgtrInstCdNm", "sprvsnInstCdNm", "sprvsnInstPicNm", "operInstCdNm", "operInstPicNm",
    "bizPrdBgngYmd", "bizPrdEndYmd", "bizPrdEtcCn", "plcyAplyMthdCn", "srngMthdCn", "aplyUrlAddr",
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


def fetch_page(page_num: int, max_retries: int = 3) -> dict:
    """온통청년 API가 가끔 500을 던지는 경우가 있어 짧은 대기 후 재시도한다."""
    params = {
        "apiKeyNm": API_KEY,
        "pageNum": page_num,
        "pageSize": PAGE_SIZE,
        "rtnType": "json",
    }
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(API_URL, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 * attempt
                print(f"  [page {page_num}] 요청 실패 ({e}), {wait}초 후 재시도 ({attempt}/{max_retries})")
                time.sleep(wait)
    raise last_error


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


def transform_value(col: str, val):
    if col == "source":
        return "ONTONG"  # 이 스크립트로 적재되는 건 전부 온통청년 API 출처
    if col in ("sprtSclCnt", "sprtTrgtMinAge", "sprtTrgtMaxAge",
                "earnMinAmt", "earnMaxAmt", "inqCnt"):
        return parse_int(val)
    if col in ("frstRegDt", "lastMdfcnDt"):
        return parse_datetime(val)
    if val is None:
        return "" if col in NOT_NULL_TEXT_DEFAULTS else None
    if isinstance(val, str):
        return val.strip()
    return val


def row_from_item(item: dict) -> tuple:
    return tuple(transform_value(col, item.get(col)) for col in COLUMNS)


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


def backfill_columns_batch(conn, columns: list, rows: list):
    """rows: [(col1_val, col2_val, ..., plcyNo), ...] (columns 순서 + 마지막에 plcyNo)"""
    if not rows:
        return
    set_clause = ", ".join(f"`{c}` = %s" for c in columns)
    sql = f"UPDATE policy SET {set_clause} WHERE plcyNo = %s"
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()


def run_backfill(conn, columns: list, start_page: int = 1):
    """전체 재적재 없이 plcyNo로 매칭해서 지정한 컬럼만 채워 넣는다.
    수동추가 정책(plcyNo 없음)은 매칭 대상이 아니라 건드리지 않고,
    다른 컬럼(관리자가 수정했을 수 있는 값 포함)도 건드리지 않는다.
    start_page: 중간에 실패했을 때 처음부터 다시 돌리지 않고 이어서 하려면 지정."""
    unknown = [c for c in columns if c not in COLUMNS]
    if unknown:
        sys.exit(f"COLUMNS에 없는 컬럼입니다: {unknown}")

    page_num = start_page
    total_updated = 0
    total_count = None

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

        rows = [
            tuple(transform_value(c, item.get(c)) for c in columns) + (item.get("plcyNo"),)
            for item in items
            if item.get("plcyNo")
        ]
        backfill_columns_batch(conn, columns, rows)
        total_updated += len(rows)
        print(f"[page {page_num}] {len(rows)}건 업데이트 (누적 {total_updated}건)")

        if total_count > 0 and page_num * PAGE_SIZE >= total_count:
            break
        if len(items) < PAGE_SIZE:
            break

        page_num += 1
        time.sleep(0.3)

    print(f"백필 완료. 총 {total_updated}건 업데이트 ({', '.join(columns)}).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--peek", action="store_true", help="1페이지만 조회해서 원본 응답 구조 출력")
    parser.add_argument(
        "--backfill-columns",
        help="전체 재적재 대신 지정한 컬럼만 plcyNo 매칭으로 UPDATE (쉼표로 여러 개 지정, 예: rgtrInstCdNm,sprvsnInstCdNm)",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="--backfill-columns 중간에 실패했을 때 이어서 시작할 페이지 번호",
    )
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

    try:
        if args.backfill_columns:
            columns = [c.strip() for c in args.backfill_columns.split(",") if c.strip()]
            run_backfill(conn, columns, start_page=args.start_page)
            return

        page_num = 1
        total_inserted = 0
        total_count = None
        all_items = []  # 이후 policy_region 매핑에 재사용 (zipCd는 COLUMNS에 없어 policy 테이블엔 안 들어감)

        while True:
            raw = fetch_page(page_num)

            if total_count is None:
                total_count = get_total_count(raw)
                if total_count > 0:
                    print(f"전체 공고 건수: {total_count}")
                    print(f"TOTAL_COUNT:{total_count}")  # external_sync.py가 파싱해 관리자 화면에 작업량으로 표시

            items = extract_items(raw)
            if not items:
                print("더 이상 데이터 없음. 종료.")
                break

            rows = [row_from_item(item) for item in items]
            insert_batch(conn, rows)
            all_items.extend(items)
            total_inserted += len(rows)
            print(f"[page {page_num}] {len(rows)}건 처리 (누적 {total_inserted}건)")

            if total_count > 0 and total_inserted >= total_count:
                break
            if len(items) < PAGE_SIZE:
                break

            page_num += 1
            time.sleep(0.3)  # API 과호출 방지

        print(f"완료. 총 {total_inserted}건 적재/업데이트.")

        # policy_region 동기화: 이 스크립트는 zipCd를 policy 테이블에 반영하지 않으므로,
        # 여기서 방금 적재/갱신한 항목들의 zipCd를 policy_region에 채워준다
        # (load_policy_regions.py를 별도 파일 경로로 수동 실행해야 했던 것을 자동화).
        print("policy_region 동기화 중...")
        plcyno_map = build_plcyno_to_id_map(conn)
        pairs, missing_policy, empty_zip = build_region_pairs(all_items, plcyno_map)
        inserted = insert_pairs(conn, pairs)
        print(
            f"policy_region: {inserted}건 적재 시도 "
            f"(정책 매칭 실패 {missing_policy}건, zipCd 없음 {empty_zip}건)"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()