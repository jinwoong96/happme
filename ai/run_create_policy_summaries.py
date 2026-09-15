# watsonx.ai로 정책 지원내용 요약(summary)만 생성
#
# policy_cards 전체(title/apply_period_type/apply_period/target/link)가 아니라
# support_summary 하나만 필요할 때 쓴다. policy_cards.json에 이미 support_summary가
# 있는 정책은 watsonx를 다시 부르지 않고 그 값을 그대로 재사용하고, 없는 정책만 새로
# 생성한다.
#
# 정책 원본은 항상 data/policy_list.json(온통청년 컬럼 체계로 미리 만들어둔 최종 정책
# 목록 파일)에서 읽는다 - 이 파일이 DB보다 먼저 만들어지고 항상 최신/완전하다고
# 가정하므로, DB 값으로 이 파일의 부족한 필드를 채우려 하지 않는다. DB는 오직 "이 정책은
# 이미 summary가 채워져 있는가"만 확인하는 용도로만 조회한다(이어하기용 existence 체크).
#
# 결과는 result/policy_summaries.json에 저장만 하고 DB에는 쓰지 않는다.
# backend/backfill_policy_summary.py가 이 파일을 읽어 policy.summary 컬럼에 반영한다.
#
# 실행 위치: ai/
# 사용법: python run_create_policy_summaries.py

import json
import os
import time
from pathlib import Path

import pymysql
from dotenv import load_dotenv

from policy_card_generator import WatsonxPolicySummaryGenerator, load_policies

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
}

INPUT_FILE = "data/policy_list.json"
POLICY_CARDS_FILE = "../backend/policy_cards.json"
OUTPUT_FILE = "result/policy_summaries.json"
ERROR_FILE = "result/policy_summaries_errors.json"

# 소규모 테스트: TEST_LIMIT건만 먼저 생성해서 품질 확인. 전체 실행하려면 None으로 변경.
TEST_LIMIT = None

BATCH_SIZE = 5
SLEEP_SEC = 0.2


def get_plcyno_with_summary_in_db() -> set[str]:
    """DB에 이미 summary가 채워진 plcyNo만 조회한다(내용은 안 읽음, 존재 여부만)."""
    conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT plcyNo FROM policy WHERE summary IS NOT NULL AND summary != ''")
            return {row["plcyNo"] for row in cursor.fetchall() if row.get("plcyNo")}
    finally:
        conn.close()


def get_summaries_from_policy_cards() -> dict[str, str]:
    """policy_cards.json에 이미 있는 support_summary를 plcyNo 기준으로 모은다."""
    path = Path(POLICY_CARDS_FILE)
    if not path.exists():
        print(f"  {POLICY_CARDS_FILE}이 없어 건너뜁니다(전부 watsonx로 생성합니다).")
        return {}
    with open(path, encoding="utf-8") as f:
        cards = json.load(f)
    return {
        str(c.get("plcyNo")): c["support_summary"]
        for c in cards
        if c.get("plcyNo") and (c.get("support_summary") or "").strip()
    }


def load_existing_json(path, default):
    """JSON 파일을 읽는다. 파일이 없으면 default를 반환한다."""
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """데이터를 JSON 파일로 저장한다(폴더가 없으면 만든다)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """지원내용이 있는 정책을 배치로 돌며 summary를 채운다. policy_cards.json에 이미 있는
    요약은 재사용하고, 없는 정책만 watsonx로 새로 생성한다. 배치마다 바로 저장한다."""
    policies = load_policies(INPUT_FILE)
    # 지원 내용이 비어있으면 요약할 게 없으므로 제외한다.
    policies = [p for p in policies if (p.get("plcySprtCn") or "").strip()]
    if TEST_LIMIT is not None:
        policies = policies[:TEST_LIMIT]

    results = load_existing_json(OUTPUT_FILE, [])
    errors = load_existing_json(ERROR_FILE, [])
    done_ids = {item.get("plcyNo") for item in results}
    done_ids |= get_plcyno_with_summary_in_db()

    card_summaries = get_summaries_from_policy_cards()

    generator = WatsonxPolicySummaryGenerator()

    print(f"정책 목록 파일 정책 수: {len(policies)}")
    print(f"이미 처리됨(파일+DB): {len(done_ids)}")
    print(f"policy_cards.json에서 재사용 가능한 요약: {len(card_summaries)}건")

    total_batches = (len(policies) - 1) // BATCH_SIZE + 1 if policies else 0
    reused_count = 0
    generated_count = 0

    for batch_idx, start in enumerate(range(0, len(policies), BATCH_SIZE), start=1):
        batch = [p for p in policies[start:start + BATCH_SIZE] if p.get("plcyNo") not in done_ids]

        if not batch:
            print(f"\n===== Batch {batch_idx}/{total_batches} SKIP =====")
            continue

        print(f"\n===== Batch {batch_idx}/{total_batches} 생성 시작 =====")

        for policy in batch:
            plcy_no = policy.get("plcyNo", "")
            policy_name = policy.get("plcyNm", "")

            # policy_cards.json에 이미 있으면 watsonx 호출 없이 그대로 재사용한다.
            existing_summary = card_summaries.get(plcy_no)
            if existing_summary:
                print(f"  재사용: {policy_name}")
                results.append({"plcyNo": plcy_no, "support_summary": existing_summary})
                done_ids.add(plcy_no)
                reused_count += 1
                continue

            try:
                print(f"  생성 중: {policy_name}")
                summary_result = generator.summarize_one(policy)
                results.append({
                    "plcyNo": plcy_no,
                    "support_summary": summary_result.get("support_summary", ""),
                })
                done_ids.add(plcy_no)
                generated_count += 1
            except Exception as e:
                errors.append({"plcyNo": plcy_no, "policy_name": policy_name, "error": str(e)})
                print(f"  실패: {policy_name} / {e}")

            if SLEEP_SEC > 0:
                time.sleep(SLEEP_SEC)

        save_json(OUTPUT_FILE, results)
        save_json(ERROR_FILE, errors)
        print(f"Batch {batch_idx} 저장 완료 (누적 성공 {len(results)}, 실패 {len(errors)})")

    print("\n생성 완료")
    print(f"policy_cards.json 재사용: {reused_count}개")
    print(f"watsonx 신규 생성: {generated_count}개")
    print(f"생성 실패: {len(errors)}개")
    print(f"결과 저장: {OUTPUT_FILE}")
    print(f"오류 저장: {ERROR_FILE}")


if __name__ == "__main__":
    main()
