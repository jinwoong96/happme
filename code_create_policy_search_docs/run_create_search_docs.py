### watsonx.ai로 정책 문서 생성 (상위 코드)
# run_create_search_docs.py

from pathlib import Path

from code_create_policy_search_docs.search_doc_generator_watsonx import (
    WatsonxSearchDocGenerator,
    load_policies,
    save_json,
)


INPUT_FILE = "data/policy_list.json"
OUTPUT_FILE = "result/search_docs_watsonx.json"
ERROR_FILE = "result/search_docs_watsonx_errors.json"

# 전체 생성하려면 START = 1, END = None
START = 1
END = None

BATCH_SIZE = 5
SLEEP_SEC = 0.2


def load_existing_json(path, default):
    path = Path(path)
    if not path.exists():
        return default

    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    policies = load_policies(INPUT_FILE)

    start_idx = START - 1

    if END is None:
        end_idx = len(policies)
    else:
        end_idx = min(END, len(policies))

    selected_policies = policies[start_idx:end_idx]

    results = load_existing_json(OUTPUT_FILE, [])
    errors = load_existing_json(ERROR_FILE, [])

    done_ids = {item.get("policy_id") for item in results}

    generator = WatsonxSearchDocGenerator()

    print(f"전체 정책 수: {len(policies)}")
    print(f"생성 범위: {START} ~ {END if END is not None else len(policies)}")
    print(f"선택 정책 수: {len(selected_policies)}")
    print(f"기존 생성 수: {len(done_ids)}")

    total_batches = (len(selected_policies) - 1) // BATCH_SIZE + 1

    for batch_idx, start in enumerate(range(0, len(selected_policies), BATCH_SIZE), start=1):
        batch = selected_policies[start:start + BATCH_SIZE]

        # 이미 생성된 정책은 skip
        batch = [
            policy for policy in batch
            if policy.get("plcyNo") not in done_ids
        ]

        if not batch:
            print(f"\n===== Batch {batch_idx}/{total_batches} SKIP =====")
            continue

        print(f"\n===== Batch {batch_idx}/{total_batches} 생성 시작 =====")

        batch_results, batch_errors = generator.create_search_docs(
            batch,
            sleep_sec=SLEEP_SEC,
            verbose=True,
        )

        results.extend(batch_results)
        errors.extend(batch_errors)

        for item in batch_results:
            done_ids.add(item.get("policy_id"))

        save_json(OUTPUT_FILE, results)
        save_json(ERROR_FILE, errors)

        print(f"Batch {batch_idx} 저장 완료")
        print(f"누적 성공: {len(results)}개")
        print(f"누적 실패: {len(errors)}개")

    print("\n전체 생성 완료")
    print(f"생성 성공: {len(results)}개")
    print(f"생성 실패: {len(errors)}개")
    print(f"결과 저장: {OUTPUT_FILE}")
    print(f"오류 저장: {ERROR_FILE}")


if __name__ == "__main__":
    main()