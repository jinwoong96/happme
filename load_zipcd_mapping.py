"""
zipcd_mapping.csv -> zipcd 테이블 적재 스크립트
------------------------------------------------
CSV 컬럼: 시군구코드, 지역명
  예) 11110, 서울특별시 종로구

지역명("서울특별시 종로구")을 매번 공백 기준으로 나눠 쓰지 않도록,
sido_name(광역)/sigungu_name(기초)을 미리 분리해서 별도 컬럼에 저장한다.

실행 전 준비:
    - scenario_to_testprofile.py와 같은 폴더에 zipcd_mapping.csv 위치
    - .env에 기존 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME 값 존재

실행:
    pip install sqlalchemy pymysql python-dotenv
    python load_zipcd_mapping.py
"""

import os
import csv

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zipcd_mapping.csv")

missing = [k for k, v in {
    "DB_HOST": DB_HOST, "DB_USER": DB_USER, "DB_PASSWORD": DB_PASSWORD, "DB_NAME": DB_NAME,
}.items() if not v]
if missing:
    raise SystemExit(f".env에 다음 값이 비어있습니다: {', '.join(missing)}")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS zipcd (
    sigungu_code VARCHAR(10) PRIMARY KEY,
    sido_name    VARCHAR(50) NOT NULL,
    sigungu_name VARCHAR(50) NOT NULL,
    full_name    VARCHAR(100) NOT NULL,
    INDEX idx_sigungu_name (sigungu_name),
    INDEX idx_sido_name (sido_name)
)
"""

UPSERT_SQL = text("""
    INSERT INTO zipcd (sigungu_code, sido_name, sigungu_name, full_name)
    VALUES (:code, :sido, :sigungu, :full_name)
    ON DUPLICATE KEY UPDATE
        sido_name = :sido, sigungu_name = :sigungu, full_name = :full_name
""")


def split_region_name(full_name: str):
    """
    "서울특별시 종로구" -> ("서울특별시", "종로구")
    "세종특별자치시" 처럼 광역=기초가 같은 특수 케이스는 sigungu_name도 동일하게 채움.
    """
    parts = full_name.split(" ", 1)
    sido = parts[0]
    sigungu = parts[1] if len(parts) > 1 else parts[0]
    return sido, sigungu


def main():
    """zipcd 테이블을 만들고, CSV의 시군구코드/지역명을 시도명/시군구명으로 나눠 적재한다."""
    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}")

    with engine.connect() as conn:
        conn.execute(text(CREATE_TABLE_SQL))
        conn.commit()

    inserted = 0
    skipped = 0

    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # 컬럼명 유연하게 처리 (한글 컬럼명이 BOM/공백 등으로 깨지는 경우 대비)
        fieldnames = [name.strip() for name in reader.fieldnames]
        code_col = next((c for c in fieldnames if "코드" in c), None)
        name_col = next((c for c in fieldnames if "지역명" in c or "명" in c), None)

        if not code_col or not name_col:
            raise SystemExit(
                f"CSV 컬럼을 인식하지 못했습니다. 실제 컬럼: {reader.fieldnames}"
            )

        with engine.connect() as conn:
            for row in reader:
                code = (row.get(code_col) or "").strip()
                full_name = (row.get(name_col) or "").strip()

                if not code or not full_name:
                    skipped += 1
                    continue

                sido, sigungu = split_region_name(full_name)

                conn.execute(UPSERT_SQL, {
                    "code": code, "sido": sido, "sigungu": sigungu, "full_name": full_name,
                })
                inserted += 1

            conn.commit()

    print(f"✅ 완료: {inserted}건 적재, {skipped}건 스킵 (빈 값)")

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM zipcd")).scalar()
    print(f"현재 zipcd 총 row 수: {total}")


if __name__ == "__main__":
    main()