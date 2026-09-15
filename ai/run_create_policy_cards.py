# watsonx.ai로 정책 카드 전체를 생성하는 실행 스크립트 (policy_card_generator.py를 배치로 돌린다)

from pathlib import Path

from policy_card_generator import (
    WatsonxPolicySummaryGenerator,
    load_policies,
    save_json,
)


INPUT_FILE = "data/policy_list.json"
OUTPUT_FILE = "result/policy_cards.json"
ERROR_FILE = "result/policy_cards_errors.json"

# 소규모 테스트: TEST_LIMIT건만 먼저 생성해서 품질 확인.
# 전체 실행하려면 TEST_LIMIT = None 으로 변경.
TEST_LIMIT = None

BATCH_SIZE = 5
SLEEP_SEC = 0.2


def load_existing_json(path, default):
    """JSON 파일을 읽는다. 파일이 없으면 default를 반환한다."""
    path = Path(path)
    if not path.exists():
        return default

    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """전체 정책을 배치 단위로 나눠 카드를 생성한다. 이미 생성된 정책(done_ids)은 건너뛰고,
    배치마다 바로 저장하므로 중간에 중단돼도 이어서 실행할 수 있다."""
    policies = load_policies(INPUT_FILE)

    if TEST_LIMIT is not None:
        policies = policies[:TEST_LIMIT]

    results = load_existing_json(OUTPUT_FILE, [])
    errors = load_existing_json(ERROR_FILE, [])

    done_ids = {item.get("plcyNo") for item in results}

    generator = WatsonxPolicySummaryGenerator()

    print(f"대상 정책 수: {len(policies)}")
    print(f"기존 생성 수: {len(done_ids)}")

    total_batches = (len(policies) - 1) // BATCH_SIZE + 1 if policies else 0

    for batch_idx, start in enumerate(range(0, len(policies), BATCH_SIZE), start=1):
        batch = policies[start:start + BATCH_SIZE]

        # 이미 생성된 정책은 skip
        batch = [
            policy for policy in batch
            if policy.get("plcyNo") not in done_ids
        ]

        if not batch:
            print(f"\n===== Batch {batch_idx}/{total_batches} SKIP =====")
            continue

        print(f"\n===== Batch {batch_idx}/{total_batches} 생성 시작 =====")

        batch_results, batch_errors = generator.create_policy_cards(
            batch,
            sleep_sec=SLEEP_SEC,
            verbose=True,
        )

        results.extend(batch_results)
        errors.extend(batch_errors)

        for item in batch_results:
            done_ids.add(item.get("plcyNo"))

        save_json(OUTPUT_FILE, results)
        save_json(ERROR_FILE, errors)

        print(f"Batch {batch_idx} 저장 완료")
        print(f"누적 성공: {len(results)}개")
        print(f"누적 실패: {len(errors)}개")

    print("\n생성 완료")
    print(f"생성 성공: {len(results)}개")
    print(f"생성 실패: {len(errors)}개")
    print(f"결과 저장: {OUTPUT_FILE}")
    print(f"오류 저장: {ERROR_FILE}")


if __name__ == "__main__":
    main()
