"""
저장해둔 온통청년 API 원본 JSON에서 zipCd를 읽어 policy_region 테이블에 적재하는 스크립트.

policy_region (policy_id, zip_code)는 policy : zipCd = 1:N 관계를 표현하는 매핑 테이블.
zipCd 필드는 콤마로 구분된 여러 우편번호 문자열 (예: "11110,11140,11170").

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 policy 적재 때 쓰던 것 그대로 사용)

사용법:
    python load_policy_regions.py --path "./policy_raw.json"       # 파일 1개
    python load_policy_regions.py --path "./raw_json_dir"          # 폴더 (여러 파일 재귀 탐색)
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


def find_record_list(data):
    """
    원본 JSON이 어떤 형태로 저장돼있든(순수 배열 / result.youthPolicyList / DATA 등)
    plcyNo를 가진 dict의 리스트를 찾아서 반환.
    """
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "plcyNo" in data[0]:
            return data
        # 리스트인데 plcyNo가 바로 안 보이면 내부 요소들도 재귀 탐색
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


def load_records(path: Path) -> list:
    files = [path] if path.is_file() else sorted(path.rglob("*.json"))
    if not files:
        sys.exit(f"'{path}' 에서 JSON 파일을 찾지 못했습니다.")

    all_records = []
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            raw = json.load(f)
        records = find_record_list(raw)
        if not records:
            print(f"  [경고] {fp.name}: plcyNo를 가진 레코드 리스트를 못 찾음. 스킵.")
            continue
        all_records.extend(records)
        print(f"  {fp.name}: {len(records)}건 발견")

    return all_records


def build_plcyno_to_id_map(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT policy_id, plcyNo FROM policy")
        rows = cur.fetchall()
    return {plcy_no: policy_id for policy_id, plcy_no in rows}


def build_region_pairs(records: list, plcyno_map: dict):
    pairs = []
    missing_policy = 0
    empty_zip = 0

    for rec in records:
        plcy_no = rec.get("plcyNo")
        zip_cd = rec.get("zipCd")

        policy_id = plcyno_map.get(plcy_no)
        if policy_id is None:
            missing_policy += 1
            continue

        if not zip_cd:
            empty_zip += 1
            continue

        for zc in zip_cd.split(","):
            zc = zc.strip()
            if zc:
                pairs.append((policy_id, zc))

    return pairs, missing_policy, empty_zip


def insert_pairs(conn, pairs: list, batch_size: int = 1000) -> int:
    if not pairs:
        return 0

    sql = "INSERT IGNORE INTO policy_region (policy_id, zip_code) VALUES (%s, %s)"
    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(pairs), batch_size):
            chunk = pairs[i:i + batch_size]
            cur.executemany(sql, chunk)
            total += len(chunk)
    conn.commit()
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="원본 JSON 파일 또는 폴더 경로")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        sys.exit(f"경로가 존재하지 않습니다: {path}")

    print("JSON 파일 로드 중...")
    records = load_records(path)
    print(f"총 레코드 수: {len(records)}")

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        print("policy 테이블에서 plcyNo -> policy_id 매핑 생성 중...")
        plcyno_map = build_plcyno_to_id_map(conn)
        print(f"매핑된 policy 건수: {len(plcyno_map)}")

        pairs, missing_policy, empty_zip = build_region_pairs(records, plcyno_map)
        print(f"생성된 (policy_id, zip_code) 쌍: {len(pairs)}건")
        if missing_policy:
            print(f"  [경고] policy 테이블에서 plcyNo를 못 찾아 스킵한 레코드: {missing_policy}건 "
                  f"(먼저 policy 테이블 적재가 끝났는지 확인하세요)")
        if empty_zip:
            print(f"  [정보] zipCd가 비어있어 스킵한 레코드: {empty_zip}건")

        inserted = insert_pairs(conn, pairs)
        print(f"완료. policy_region에 {inserted}건 적재 시도 (중복은 INSERT IGNORE로 자동 스킵).")

    finally:
        conn.close()


if __name__ == "__main__":
    main()