"""
ai_schedule_cache.json -> policy_schedule 테이블 마이그레이션 스크립트

실행 위치: bene_backend 프로젝트 루트 (main.py와 같은 위치)
실행 방법: python migrate_schedule.py

전제:
- app/db/database.py 안에 AsyncSessionLocal 이 정의되어 있음
  (main.py에서 `from app.db.database import Base, async_engine, AsyncSessionLocal` 로 쓰는 걸 확인함)
- policy_schedule 테이블이 이미 생성되어 있음 (scheduleId, plcyNo, eventType, eventDate, rawText, ...)
- policy 테이블에 이미 해당 plcyNo 들이 존재함 (FK 제약조건 때문에 없으면 insert 실패)
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import text

from app.db.database import AsyncSessionLocal

# JSON 파일 경로 - 필요하면 여기만 바꿔서 쓰세요
JSON_PATH = Path("ai_schedule_cache.json")

# 허용된 이벤트 타입 (test.py의 SYSTEM_PROMPT와 동일하게 맞춤 - 방어적으로 한번 더 필터)
ALLOWED_TYPES = {"서류심사", "결과발표", "면접", "서류등록", "배치통보", "사업개시", "기수별기간"}


async def get_existing_plcy_nos(session) -> set:
    """policy 테이블에 실제로 존재하는 plcyNo만 추려서 FK 에러 방지"""
    result = await session.execute(text("SELECT plcyNo FROM policy"))
    return {row[0] for row in result.fetchall()}


async def get_already_migrated_plcy_nos(session) -> set:
    """이미 policy_schedule에 들어가 있는 plcyNo (재실행 시 중복 방지)"""
    result = await session.execute(text("SELECT DISTINCT plcyNo FROM policy_schedule"))
    return {row[0] for row in result.fetchall()}


async def migrate():
    if not JSON_PATH.exists():
        print(f"파일을 찾을 수 없습니다: {JSON_PATH.resolve()}")
        print("JSON_PATH 변수를 실제 파일 위치로 수정해주세요.")
        return

    cache = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"캐시 파일 로드 완료: 총 {len(cache)}개 정책")

    async with AsyncSessionLocal() as session:
        valid_plcy_nos = await get_existing_plcy_nos(session)
        already_migrated = await get_already_migrated_plcy_nos(session)
        print(f"policy 테이블에 존재하는 정책 수: {len(valid_plcy_nos)}")
        print(f"이미 마이그레이션된 정책 수: {len(already_migrated)}")

        inserted = 0
        skipped_no_policy = 0
        skipped_already_done = 0
        skipped_error_entry = 0
        skipped_bad_type = 0

        insert_sql = text("""
            INSERT INTO policy_schedule (plcyNo, eventType, eventDate, rawText)
            VALUES (:plcyNo, :eventType, :eventDate, :rawText)
        """)

        rows_to_insert = []

        for plcy_no, events in cache.items():
            if plcy_no not in valid_plcy_nos:
                skipped_no_policy += 1
                continue

            if plcy_no in already_migrated:
                skipped_already_done += 1
                continue

            # test.py에서 실패한 항목은 {"error": "..."} 형태로 저장돼 있었음
            if isinstance(events, dict) and "error" in events:
                skipped_error_entry += 1
                continue

            if not isinstance(events, list):
                continue

            for e in events:
                event_type = e.get("type", "")
                if event_type not in ALLOWED_TYPES:
                    skipped_bad_type += 1
                    continue

                rows_to_insert.append({
                    "plcyNo": plcy_no,
                    "eventType": event_type,
                    "eventDate": e.get("date", ""),
                    "rawText": (e.get("raw_text") or "")[:255],  # VARCHAR(255) 초과 방지
                })

        # 배치로 insert
        if rows_to_insert:
            for row in rows_to_insert:
                await session.execute(insert_sql, row)
            await session.commit()
            inserted = len(rows_to_insert)

        print("\n=== 마이그레이션 완료 ===")
        print(f"삽입된 일정 row 수: {inserted}")
        print(f"policy에 없는 plcyNo라 스킵: {skipped_no_policy}")
        print(f"이미 마이그레이션되어 스킵: {skipped_already_done}")
        print(f"에러 항목이라 스킵: {skipped_error_entry}")
        print(f"허용되지 않은 type이라 스킵: {skipped_bad_type}")


if __name__ == "__main__":
    asyncio.run(migrate())