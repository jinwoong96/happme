"""
ai/run_create_policy_summaries.py가 만든 result/policy_summaries.json을 읽어
policy.summary 컬럼(watsonx로 생성한 지원내용 요약)에 반영하는 백필 스크립트.

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 policy 적재 때 쓰던 것 그대로 사용)

사용법:
    python backfill_policy_summary.py                  # 실제로 DB에 반영
    python backfill_policy_summary.py --dry-run         # DB에 반영하지 않고 결과만 미리보기
    python backfill_policy_summary.py --input <path>    # 입력 파일 경로 지정 (기본: ../ai/result/policy_summaries.json)
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

DEFAULT_INPUT_FILE = "../ai/result/policy_summaries.json"


def ensure_summary_column(conn) -> None:
    """Base.metadata.create_all은 기존 테이블에 새 컬럼을 추가해주지 않으므로 직접 확인 후 추가."""
    with conn.cursor() as cur:
        cur.execute("SHOW COLUMNS FROM policy LIKE 'summary'")
        if cur.fetchone() is None:
            print("  policy.summary 컬럼이 없어 추가합니다...")
            cur.execute("ALTER TABLE policy ADD COLUMN summary TEXT NULL")
    conn.commit()


def load_summaries(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def backfill(conn, items: list[dict], dry_run: bool) -> None:
    ensure_summary_column(conn)

    pairs = [
        (item["support_summary"], item["plcyNo"])
        for item in items
        if item.get("support_summary") and item.get("plcyNo")
    ]

    print(f"입력 항목 수: {len(items)}")
    print(f"반영할 항목 수: {len(pairs)}")

    if dry_run:
        print("\n[--dry-run] 미리보기 10건:")
        for summary, plcy_no in pairs[:10]:
            print(f"  plcyNo={plcy_no}: {summary[:60]}")
        print("\nDB에는 반영하지 않았습니다 (--dry-run).")
        return

    if not pairs:
        print("업데이트할 항목이 없습니다.")
        return

    sql = "UPDATE policy SET summary = %s WHERE plcyNo = %s"
    with conn.cursor() as cur:
        cur.executemany(sql, pairs)
    conn.commit()
    print(f"{len(pairs)}건 업데이트 완료.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB에 반영하지 않고 결과만 미리보기")
    parser.add_argument("--input", default=DEFAULT_INPUT_FILE, help="policy_summaries.json 경로")
    args = parser.parse_args()

    items = load_summaries(args.input)

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        backfill(conn, items, args.dry_run)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
