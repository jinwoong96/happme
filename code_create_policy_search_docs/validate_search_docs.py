### 생성된 정책 문서 이상치 검증
# validate_search_docs.py

import json
import re
from pathlib import Path
from collections import Counter


INPUT_FILE = "result/search_docs_watsonx.json"
REPORT_FILE = "result/search_docs_validation_report.json"
SUMMARY_FILE = "result/search_docs_validation_summary.txt"


REQUIRED_FIELDS = [
    "policy_id",
    "policy_name",
    "summary",
    "target",
    "support",
    "keywords",
    "situations",
    "example_queries",
    "search_text",
]

LIST_FIELDS = [
    "target",
    "support",
    "keywords",
    "situations",
    "example_queries",
]

SUSPICIOUS_TARGET_WORDS = [
    "전문가",
    "기관 관계자",
    "유관기관",
    "발표자",
    "담당자",
    "수행기관",
    "운영기관",
    "참석자",
]

GENERIC_KEYWORDS = [
    "신청",
    "문의",
    "절차",
    "안내",
    "정보 제공",
    "서비스 제공",
]

BAD_TEXT_PATTERNS = [
    "Cover",
    "한 도어",
    "보아이던",
    "지원 절차 안내 문의",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_issue(issues, level, field, message):
    issues.append({
        "level": level,
        "field": field,
        "message": message,
    })


def has_repeated_phrase(text):
    words = re.findall(r"[가-힣A-Za-z0-9]+", text)
    if len(words) < 8:
        return False

    counter = Counter(words)
    repeated = [word for word, count in counter.items() if count >= 5 and len(word) >= 2]
    return len(repeated) > 0


def validate_doc(doc):
    issues = []

    # 필수 필드 검사
    for field in REQUIRED_FIELDS:
        if field not in doc:
            add_issue(issues, "error", field, "필수 필드가 없습니다.")

    policy_id = doc.get("policy_id", "")
    policy_name = doc.get("policy_name", "")

    if not policy_id:
        add_issue(issues, "error", "policy_id", "policy_id가 비어 있습니다.")

    if not policy_name:
        add_issue(issues, "error", "policy_name", "policy_name이 비어 있습니다.")

    # 문자열 필드 검사
    for field in ["summary", "search_text"]:
        value = doc.get(field)

        if not isinstance(value, str):
            add_issue(issues, "error", field, "문자열이 아닙니다.")
            continue

        value = value.strip()

        if not value:
            add_issue(issues, "error", field, "값이 비어 있습니다.")

        if field == "summary":
            if len(value) < 15:
                add_issue(issues, "warning", field, "summary가 너무 짧습니다.")
            if len(value) > 250:
                add_issue(issues, "warning", field, "summary가 너무 깁니다.")

        if field == "search_text":
            if len(value) < 40:
                add_issue(issues, "warning", field, "search_text가 너무 짧습니다.")
            if len(value) > 700:
                add_issue(issues, "warning", field, "search_text가 너무 깁니다.")

        for pattern in BAD_TEXT_PATTERNS:
            if pattern in value:
                add_issue(issues, "error", field, f"이상 표현이 포함되어 있습니다: {pattern}")

        if has_repeated_phrase(value):
            add_issue(issues, "warning", field, "반복 표현이 의심됩니다.")

    # 리스트 필드 검사
    for field in LIST_FIELDS:
        value = doc.get(field)

        if not isinstance(value, list):
            add_issue(issues, "error", field, "리스트가 아닙니다.")
            continue

        if field in ["support", "keywords", "situations", "example_queries"] and len(value) == 0:
            add_issue(issues, "warning", field, "값이 비어 있습니다.")

        if field == "keywords":
            if len(value) > 10:
                add_issue(issues, "error", field, f"keywords가 너무 많습니다: {len(value)}개")
            if len(value) < 3:
                add_issue(issues, "warning", field, "keywords가 너무 적습니다.")

        if field == "situations":
            if len(value) > 6:
                add_issue(issues, "warning", field, f"situations가 많습니다: {len(value)}개")

        if field == "example_queries":
            if len(value) > 6:
                add_issue(issues, "warning", field, f"example_queries가 많습니다: {len(value)}개")

        # 중복 검사
        cleaned = [str(x).strip() for x in value if str(x).strip()]
        if len(cleaned) != len(set(cleaned)):
            add_issue(issues, "warning", field, "중복 항목이 있습니다.")

        for item in cleaned:
            if len(item) > 120:
                add_issue(issues, "warning", field, f"항목이 너무 깁니다: {item[:80]}...")

            for pattern in BAD_TEXT_PATTERNS:
                if pattern in item:
                    add_issue(issues, "error", field, f"이상 표현이 포함되어 있습니다: {pattern}")

            if has_repeated_phrase(item):
                add_issue(issues, "warning", field, f"반복 표현이 의심됩니다: {item[:80]}...")

        # target 의심 표현
        if field == "target":
            for item in cleaned:
                for word in SUSPICIOUS_TARGET_WORDS:
                    if word in item:
                        add_issue(
                            issues,
                            "warning",
                            field,
                            f"target에 행사 구성원/기관 표현이 포함되어 있을 수 있습니다: {item}"
                        )

        # keywords 일반 표현 반복
        if field == "keywords":
            for item in cleaned:
                for word in GENERIC_KEYWORDS:
                    if word in item:
                        add_issue(
                            issues,
                            "warning",
                            field,
                            f"keywords에 일반 행정 표현이 포함되어 있습니다: {item}"
                        )

    return {
        "policy_id": policy_id,
        "policy_name": policy_name,
        "issue_count": len(issues),
        "issues": issues,
    }


def main():
    docs = load_json(INPUT_FILE)

    if not isinstance(docs, list):
        raise ValueError("입력 파일은 JSON 리스트여야 합니다.")

    reports = []
    issue_docs = []

    for doc in docs:
        report = validate_doc(doc)
        reports.append(report)

        if report["issue_count"] > 0:
            issue_docs.append(report)

    total_docs = len(docs)
    issue_doc_count = len(issue_docs)

    level_counter = Counter()
    field_counter = Counter()

    for report in reports:
        for issue in report["issues"]:
            level_counter[issue["level"]] += 1
            field_counter[issue["field"]] += 1

    result = {
        "total_docs": total_docs,
        "issue_doc_count": issue_doc_count,
        "clean_doc_count": total_docs - issue_doc_count,
        "level_counts": dict(level_counter),
        "field_counts": dict(field_counter),
        "issue_docs": issue_docs,
    }

    save_json(REPORT_FILE, result)

    summary_lines = [
        f"전체 문서 수: {total_docs}",
        f"문제 의심 문서 수: {issue_doc_count}",
        f"정상 문서 수: {total_docs - issue_doc_count}",
        "",
        "[이슈 레벨별 개수]",
        *[f"- {k}: {v}" for k, v in level_counter.items()],
        "",
        "[필드별 이슈 개수]",
        *[f"- {k}: {v}" for k, v in field_counter.most_common()],
        "",
        f"상세 리포트 저장: {REPORT_FILE}",
    ]

    Path(SUMMARY_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()