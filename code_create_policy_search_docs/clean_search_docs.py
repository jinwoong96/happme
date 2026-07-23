# watsonx로 생성한 검색 문서 자동 정제
#
# validate_search_docs.py가 찾아내는 이슈 중 세 가지만 자동으로 고친다.
# 1) 리스트 필드(target/support/keywords/situations/example_queries) 중복 -> 자동 제거
# 2) target에 "전문가"/"담당자" 등 사람/기관을 가리키는 표현이 섞여 있는 경우 -> 자동 제외
#    (이건 원래 사람이 직접 하나씩 확인하고 고치던 부분이라, 자동 제외는 하되 무엇을
#    왜 뺐는지 별도 로그 파일에 남겨서 나중에 직접 검토할 수 있게 한다)
# 3) keywords(10개)/situations(6개)/example_queries(6개) 개수 초과 -> 앞에서부터 개수만큼만
#    남기고 자름(우선순위를 판단할 다른 근거가 없어 생성 순서를 그대로 신뢰)
#
# 그 외 이슈(필수 필드 누락, 이상 표현 패턴, 개수가 너무 적은 경우 등)는 여전히
# validate_search_docs.py가 보고만 하고 자동으로 고치지 않는다.

import json
from pathlib import Path

from code_create_policy_search_docs.validate_search_docs import SUSPICIOUS_TARGET_WORDS


INPUT_FILE = "result/search_docs_watsonx.json"
OUTPUT_FILE = "result/search_docs_watsonx_cleaned.json"
TARGET_EXCEPTION_LOG_FILE = "result/search_docs_target_exceptions_log.json"

LIST_FIELDS = ["target", "support", "keywords", "situations", "example_queries"]

# validate_search_docs.py에서 "개수 초과(error/warning)"로 잡던 것과 동일한 상한.
MAX_ITEM_COUNTS = {
    "keywords": 10,
    "situations": 6,
    "example_queries": 6,
}


def load_json(path):
    """JSON 파일을 읽는다."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """데이터를 JSON 파일로 저장한다(폴더가 없으면 만든다)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def dedupe_preserve_order(items):
    """리스트에서 중복 항목을 지우되, 처음 나온 순서는 그대로 유지한다."""
    seen = set()
    result = []
    for item in items:
        key = str(item).strip()
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def remove_suspicious_targets(doc, exceptions_log):
    """target 목록에서 "전문가"/"담당자"처럼 지원 대상이 아니라 사람/기관을 가리키는
    표현을 제거하고, 뭘 왜 뺐는지 exceptions_log에 기록한다(나중에 직접 검토하도록)."""
    target = doc.get("target")
    if not isinstance(target, list):
        return

    kept = []
    for item in target:
        matched_word = next((w for w in SUSPICIOUS_TARGET_WORDS if w in str(item)), None)
        if matched_word:
            exceptions_log.append({
                "policy_id": doc.get("policy_id", ""),
                "policy_name": doc.get("policy_name", ""),
                "removed_item": item,
                "matched_word": matched_word,
            })
        else:
            kept.append(item)
    doc["target"] = kept


def clean_doc(doc, exceptions_log):
    """검색문서 하나를 정제한다: 리스트 필드 중복 제거 -> 의심스러운 대상 표현 제거 ->
    항목별 최대 개수로 자르기."""
    for field in LIST_FIELDS:
        value = doc.get(field)
        if isinstance(value, list):
            doc[field] = dedupe_preserve_order(value)

    # target 중복 제거를 먼저 끝낸 뒤에 의심 표현을 걸러낸다.
    remove_suspicious_targets(doc, exceptions_log)

    # 중복 제거로 이미 상한 이내로 줄었을 수 있으니, 그 다음에 개수를 자른다.
    for field, max_count in MAX_ITEM_COUNTS.items():
        value = doc.get(field)
        if isinstance(value, list) and len(value) > max_count:
            doc[field] = value[:max_count]

    return doc


def main():
    """생성된 검색문서 전체를 정제하고, 결과와 target 제외 기록을 각각 파일로 저장한다."""
    docs = load_json(INPUT_FILE)
    if not isinstance(docs, list):
        raise ValueError("입력 파일은 JSON 리스트여야 합니다.")

    exceptions_log = []
    cleaned = [clean_doc(doc, exceptions_log) for doc in docs]

    save_json(OUTPUT_FILE, cleaned)
    save_json(TARGET_EXCEPTION_LOG_FILE, exceptions_log)

    print(f"전체 문서 수: {len(cleaned)}")
    print(f"target 자동 제외 건수: {len(exceptions_log)}")
    print(f"결과 저장: {OUTPUT_FILE}")
    print(f"target 제외 기록(직접 검토 필요): {TARGET_EXCEPTION_LOG_FILE}")


if __name__ == "__main__":
    main()
