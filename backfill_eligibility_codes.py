"""
ai/data/ontong_total.json.json(온통청년 원본 API 응답, plcyNo 키)을 읽어
policy 테이블의 자격조건 코드 6개 컬럼(aplyPrdSeCd/sprtTrgtAgeLmtYn/schoolCd/
plcyMajorCd/sbizCd/jobCd)을 백필하는 스크립트.

이 6개는 DB 스키마 자체에 없던 컬럼이라(온통청년 원본에만 있음), plcyNo로 매칭되는
정책만 채워진다 - BOKJIRO/MANUAL 소스 등 원본에 없는 정책은 계속 NULL로 남는다.

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 policy 적재 때 쓰던 것 그대로 사용)

사용법:
    python backfill_eligibility_codes.py             # 실제로 DB에 반영
    python backfill_eligibility_codes.py --dry-run    # DB에 반영하지 않고 결과만 미리보기
    python backfill_eligibility_codes.py --input <path>   # 입력 파일 경로 지정
"""

import os
import json
import argparse

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

DEFAULT_INPUT_FILE = "../ai/data/ontong_total.json.json"

CODE_FIELDS = ["aplyPrdSeCd", "sprtTrgtAgeLmtYn", "schoolCd", "plcyMajorCd", "sbizCd", "jobCd"]


def ensure_columns(conn) -> None:
    """Base.metadata.create_all은 기존 테이블에 새 컬럼을 추가해주지 않으므로 직접 확인 후 추가."""
    column_ddl = {
        "aplyPrdSeCd": "VARCHAR(20) NULL",
        "sprtTrgtAgeLmtYn": "CHAR(1) NULL",
        "schoolCd": "VARCHAR(100) NULL",  # 쉼표로 여러 코드 나열 가능(실측 최대 71자)
        "plcyMajorCd": "VARCHAR(100) NULL",  # 쉼표로 여러 코드 나열 가능(실측 최대 63자)
        "sbizCd": "VARCHAR(100) NULL",
        "jobCd": "VARCHAR(100) NULL",
    }
    with conn.cursor() as cur:
        for column, ddl in column_ddl.items():
            cur.execute(f"SHOW COLUMNS FROM policy LIKE '{column}'")
            if cur.fetchone() is None:
                print(f"  policy.{column} 컬럼이 없어 추가합니다...")
                cur.execute(f"ALTER TABLE policy ADD COLUMN {column} {ddl}")
    conn.commit()


def load_source_policies(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "result" in data and "youthPolicyList" in data["result"]:
            return data["result"]["youthPolicyList"]
        if "youthPolicyList" in data:
            return data["youthPolicyList"]
    raise ValueError("지원하지 않는 JSON 구조입니다.")


def backfill(conn, source_policies: list[dict], dry_run: bool) -> None:
    ensure_columns(conn)

    with conn.cursor() as cur:
        cur.execute("SELECT plcyNo FROM policy WHERE plcyNo IS NOT NULL")
        db_plcynos = {row[0] for row in cur.fetchall()}

    rows = []
    for policy in source_policies:
        plcy_no = policy.get("plcyNo")
        if not plcy_no or plcy_no not in db_plcynos:
            continue
        values = [policy.get(field) or None for field in CODE_FIELDS]
        rows.append((*values, plcy_no))

    print(f"원본 파일 정책 수: {len(source_policies)}")
    print(f"DB와 매칭되어 반영할 정책 수: {len(rows)}")

    if dry_run:
        print("\n[--dry-run] 미리보기 10건:")
        for row in rows[:10]:
            plcy_no = row[-1]
            values = dict(zip(CODE_FIELDS, row[:-1]))
            print(f"  plcyNo={plcy_no}: {values}")
        print("\nDB에는 반영하지 않았습니다 (--dry-run).")
        return

    if not rows:
        print("업데이트할 항목이 없습니다.")
        return

    sql = f"""
        UPDATE policy
        SET {', '.join(f'{field} = %s' for field in CODE_FIELDS)}
        WHERE plcyNo = %s
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    print(f"{len(rows)}건 업데이트 완료.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB에 반영하지 않고 결과만 미리보기")
    parser.add_argument("--input", default=DEFAULT_INPUT_FILE, help="온통청년 원본 JSON 경로")
    args = parser.parse_args()

    source_policies = load_source_policies(args.input)

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        backfill(conn, source_policies, args.dry_run)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
