"""
watsonx + rule-engine으로 정책별 소득 확인 필요 질문을 뽑아낸 결과(notice_Truth_2632.json)를
policy_incomeRequired 테이블에 적재하는 스크립트.

원본 JSON은 [{ plcyNo, required_fields, candidates, biz_rule_fixed, llm_verified, elapsed_sec }, ...] 형태.
이 중 plcyNo -> policy_id 매핑 후 policy_incom_id, plcyNo, required_fields를 저장.

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 policy 적재 때 쓰던 것 그대로 사용)

사용법:
    python load_income_required.py
    python load_income_required.py --json "다른경로.json"
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

DEFAULT_JSON = Path(__file__).parent / "notice_Truth_2632.json"


def build_plcyno_to_id_map(conn) -> dict:
    """전체 정책의 plcyNo -> policy_id 매핑을 만든다."""
    with conn.cursor() as cur:
        cur.execute("SELECT policy_id, plcyNo FROM policy")
        rows = cur.fetchall()
    return {plcy_no: policy_id for policy_id, plcy_no in rows}


def ensure_table(conn) -> None:
    """policy_incomeRequired 테이블이 없으면 만든다."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS policy_incomeRequired (
                policy_incom_id INT PRIMARY KEY,
                plcyNo          VARCHAR(50) NOT NULL,
                required_fields JSON NOT NULL,
                FOREIGN KEY (policy_incom_id) REFERENCES policy(policy_id)
            )
            """
        )
    conn.commit()


def load_income_required(conn, json_path: Path, plcyno_map: dict) -> int:
    """소득확인 필요 필드 결과 JSON을 읽어, plcyNo가 매칭되는 정책만 policy_incomeRequired에 적재한다."""
    print(f"{json_path.name} 에서 적재 중...")
    with open(json_path, encoding="utf-8") as f:
        records = json.load(f)

    rows = []
    missing_policy = 0
    for rec in records:
        plcy_no = rec.get("plcyNo")
        policy_id = plcyno_map.get(plcy_no)
        if policy_id is None:
            missing_policy += 1
            continue
        required_fields = rec.get("required_fields", [])
        rows.append((policy_id, plcy_no, json.dumps(required_fields, ensure_ascii=False)))

    if missing_policy:
        print(f"  [경고] policy 테이블에서 plcyNo를 못 찾아 스킵한 정책: {missing_policy}건")

    if not rows:
        print("  적재할 데이터 없음.")
        return 0

    sql = (
        "INSERT INTO policy_incomeRequired (policy_incom_id, plcyNo, required_fields) VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE plcyNo = VALUES(plcyNo), required_fields = VALUES(required_fields)"
    )
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    print(f"  {len(rows)}건 적재 완료 (기존 행은 갱신).")
    return len(rows)


def main():
    """CLI 진입점: JSON 경로를 받아 policy_incomeRequired 테이블을 채운다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(DEFAULT_JSON), help="required_fields 결과 JSON 경로")
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        sys.exit(f"JSON 경로가 존재하지 않습니다: {json_path}")

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        ensure_table(conn)
        plcyno_map = build_plcyno_to_id_map(conn)
        print(f"매핑된 policy 건수: {len(plcyno_map)}")

        load_income_required(conn, json_path, plcyno_map)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
