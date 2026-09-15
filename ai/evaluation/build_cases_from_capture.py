"""
evaluation/collected/raw_capture.jsonl(recommendation_service.py가 EVAL_CAPTURE=true일 때
남긴 실제 호출 기록)을 읽어서 situation_selection_cases.json / situation_explain_cases.json에
이어붙이는 변환 스크립트.

raw_capture.jsonl 한 줄 = recommend_chat_svc 한 번 호출:
    {"ts", "chat", "candidates": [...10개 정책명...], "llm_response": "3"(또는 "0"),
     "reference": null, "context": "..." 또는 null, "answer": "..." 또는 null}

이 스크립트가 하는 일
1. 매 줄을 situation_selection_cases.json용 케이스로 변환 (reference는 항상 null로 남음
   -> 사람이 직접 "이 상황엔 몇 번이 진짜 정답인가"를 채워야 함)
2. context/answer가 둘 다 있는 줄(=정책이 실제로 선택된 경우)만 추가로
   situation_explain_cases.json용 케이스로도 변환 (여긴 정답 라벨이 필요 없어서 그대로 씀)
3. 기존 cases.json 내용에 이어붙이고(중복은 chat+candidates로 판단해 건너뜀), 저장

사용법
    1) bene_ai/.env에 EVAL_CAPTURE=true 추가하고 서버 재시작
    2) collect_cases.py로 여러 상황을 실제로 서버에 돌려서 raw_capture.jsonl 채우기
    3) python build_cases_from_capture.py 실행
    4) situation_selection_cases.json을 열어서 "reference": null인 항목마다
       실제 정답 번호를 채워넣기 (이건 사람이 판단해야 하는 부분이라 자동화 불가)
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
RAW_PATH = BASE_DIR / "collected" / "raw_capture.jsonl"
SELECTION_PATH = BASE_DIR / "test_cases" / "situation_selection_cases.json"
EXPLAIN_PATH = BASE_DIR / "test_cases" / "situation_explain_cases.json"


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def selection_key(case: dict) -> tuple:
    return (case.get("chat"), tuple(case.get("candidates") or []))


def explain_key(case: dict) -> tuple:
    return (case.get("chat"), case.get("context"))


def main():
    if not RAW_PATH.exists():
        print(f"[오류] {RAW_PATH} 이(가) 없습니다. 먼저 EVAL_CAPTURE=true로 서버를 실행해서 요청을 몇 번 보내세요.")
        return

    with open(RAW_PATH, encoding="utf-8") as f:
        raw_lines = [json.loads(line) for line in f if line.strip()]
    print(f"raw_capture.jsonl: {len(raw_lines)}건 읽음")

    selection_cases = load_json(SELECTION_PATH)
    explain_cases = load_json(EXPLAIN_PATH)

    existing_selection_keys = {selection_key(c) for c in selection_cases}
    existing_explain_keys = {explain_key(c) for c in explain_cases}

    added_selection = 0
    added_explain = 0
    next_sel_id = len(selection_cases) + 1
    next_exp_id = len(explain_cases) + 1

    for row in raw_lines:
        sel_case = {
            "case_id": f"sel_{next_sel_id:03d}",
            "chat": row.get("chat"),
            "candidates": row.get("candidates"),
            "llm_response": row.get("llm_response"),
            "reference": row.get("reference"),  # 항상 null로 캡처됨 -> 사람이 채워야 함
        }
        if selection_key(sel_case) not in existing_selection_keys:
            selection_cases.append(sel_case)
            existing_selection_keys.add(selection_key(sel_case))
            next_sel_id += 1
            added_selection += 1

        if row.get("context") and row.get("answer"):
            exp_case = {
                "case_id": f"exp_{next_exp_id:03d}",
                "chat": row.get("chat"),
                "context": row.get("context"),
                "llm_response": row.get("answer"),
            }
            if explain_key(exp_case) not in existing_explain_keys:
                explain_cases.append(exp_case)
                existing_explain_keys.add(explain_key(exp_case))
                next_exp_id += 1
                added_explain += 1

    save_json(SELECTION_PATH, selection_cases)
    save_json(EXPLAIN_PATH, explain_cases)

    print(f"선택형(situation_selection_cases.json): +{added_selection}건 (전체 {len(selection_cases)}건)")
    print(f"설명형(situation_explain_cases.json)  : +{added_explain}건 (전체 {len(explain_cases)}건)")
    if added_selection:
        print(
            f"\n[다음 할 일] {SELECTION_PATH.name}을 열어서 \"reference\": null인 항목마다 "
            "실제 정답 번호(candidates 중 몇 번, 없으면 \"0\")를 채워주세요. 이건 사람이 판단해야 해서 자동화가 안 돼요."
        )


if __name__ == "__main__":
    main()
