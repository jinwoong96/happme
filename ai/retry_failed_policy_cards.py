# 생성 실패한 정책만 골라서 재시도 (result/policy_cards_errors.json 기준)

import json
from pathlib import Path

from policy_card_generator import (
    WatsonxPolicySummaryGenerator,
    load_policies,
    save_json,
)


INPUT_FILE = "data/policy_list.json"
OUTPUT_FILE = "result/policy_cards.json"
ERROR_FILE = "result/policy_cards_errors.json"

SLEEP_SEC = 0.2

# 특정 정책만 재시도하고 싶으면 plcyNo를 여기 지정 (예: "20260618005400213241").
# None이면 errors 파일에 있는 항목을 전부 재시도한다.
TARGET_PLCY_NO = "20260406005400212413"


def load_existing_json(path, default):
    """JSON 파일을 읽는다. 파일이 없으면 default를 반환한다."""
    path = Path(path)
    if not path.exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """errors 파일(또는 TARGET_PLCY_NO 하나)에 있는 실패 정책만 골라 다시 카드를 생성하고,
    성공한 건은 results에 반영 + errors에서 제거, 이번에도 실패하면 새 에러로 남긴다."""
    results = load_existing_json(OUTPUT_FILE, [])
    errors = load_existing_json(ERROR_FILE, [])

    if not errors:
        print("재시도할 실패 항목이 없습니다.")
        return

    if TARGET_PLCY_NO is not None:
        targets = [e for e in errors if e.get("plcyNo") == TARGET_PLCY_NO]
        if not targets:
            print(f"errors 파일에서 plcyNo={TARGET_PLCY_NO} 항목을 찾지 못했습니다.")
            return
    else:
        targets = errors

    target_ids = {e.get("plcyNo") for e in targets}

    all_policies = load_policies(INPUT_FILE)
    policy_by_id = {p.get("plcyNo"): p for p in all_policies}

    retry_policies = []
    for plcy_no in target_ids:
        policy = policy_by_id.get(plcy_no)
        if policy is None:
            print(f"원본 데이터에서 plcyNo={plcy_no} 정책을 찾지 못했습니다. (스킵)")
            continue
        retry_policies.append(policy)

    print(f"재시도 대상: {len(retry_policies)}건")
    for p in retry_policies:
        print(f"  - {p.get('plcyNo')} / {p.get('plcyNm')}")

    generator = WatsonxPolicySummaryGenerator()

    new_results, new_errors = generator.create_policy_cards(
        retry_policies,
        sleep_sec=SLEEP_SEC,
        verbose=True,
    )

    # 성공한 건: errors에서 제거하고 results에 반영(기존 동일 plcyNo 있으면 교체)
    succeeded_ids = {r.get("plcyNo") for r in new_results}

    results = [r for r in results if r.get("plcyNo") not in succeeded_ids]
    results.extend(new_results)

    # 재시도 대상이었던 항목은 errors에서 우선 제거하고, 이번에도 실패했으면 새 에러로 다시 추가
    errors = [e for e in errors if e.get("plcyNo") not in target_ids]
    errors.extend(new_errors)

    save_json(OUTPUT_FILE, results)
    save_json(ERROR_FILE, errors)

    print("\n재시도 완료")
    print(f"재시도 성공: {len(new_results)}건")
    print(f"재시도 실패: {len(new_errors)}건")
    for e in new_errors:
        print(f"  - {e.get('plcyNo')} / {e.get('policy_name')}: {e.get('error')}")


if __name__ == "__main__":
    main()
