"""
1번 평가(_llm_select_candidate)를 모델별로 비교하는 스크립트.

ragas_eval.py의 evaluate_selection()은 "프로덕션에서 실제로 쓰는 모델(watsonx
mistral-small-24b) 하나가 만든 llm_response"를 정답(reference)과 비교할 뿐,
다른 모델로 선택 작업 자체를 다시 시켜보지는 않는다. 이 스크립트는 그 반대다:
recommendation_service.py의 _llm_select_candidate와 완전히 동일한 프롬프트를
4개 모델(JUDGES, ragas_eval.py와 동일한 목록) 각각에 실제로 태워서,
"어느 모델이 이 선택 작업을 더 잘하는지"를 Accuracy/Precision/Recall/F1로 비교한다.

주의: watsonx_mistral_small_24b 행은 situation_selection_cases.json의 llm_response
(실제 서버 캡처값)와 100% 같지 않을 수 있다. 여기서는 4개 모델을 공정하게 같은 조건
(temperature=0, 동일 프롬프트)으로 다시 실행하기 때문이다. 프로덕션 실측치와 비교하려면
ragas_eval.py의 1번 결과(1_selection_result.csv)를 같이 보면 된다.

사전 준비: ragas_eval.py와 동일 (requirements-eval.txt 설치, watsonx/.env, Ollama, Groq)

실행
    python evaluate_selection_models.py
"""

import json
import re
import time

import pandas as pd
from dotenv import load_dotenv

from ragas_eval import JUDGES, load_cases, SELECTION_CASES_PATH, RESULTS_DIR

load_dotenv()


def build_prompt(chat: str, candidates: list[str]) -> str:
    """recommendation_service.py._llm_select_candidate와 완전히 동일한 프롬프트."""
    listing = "\n".join(f"{i}. {name}" for i, name in enumerate(candidates, start=1))
    return f"""당신은 청년 정책 목록에서 사용자 상황에 맞는 정책을 고르는 도우미입니다.

[후보 정책 목록 (번호. 정책명)]
{listing}

[사용자 상황]
{chat}

규칙:
1. 위 후보 정책 목록 중 사용자 상황에 실제로 도움이 될 만한 정책이 있으면 그 번호 하나만 답하세요.
2. 적절한 정책이 없으면 0을 답하세요.
3. 반드시 숫자 하나만 답하세요. 다른 말은 절대 하지 마세요.

번호:"""


def call_model(langchain_llm, prompt: str) -> str:
    """WatsonxLLM은 문자열을 바로 반환, ChatOllama/ChatGroq는 AIMessage(.content)를 반환한다."""
    result = langchain_llm.invoke(prompt)
    return result.content if hasattr(result, "content") else str(result)


def parse_choice(raw: str, n_candidates: int) -> str:
    """production _llm_select_candidate와 동일한 파싱 규칙(숫자 추출, 범위 밖/실패는 0)."""
    match = re.search(r"-?\d+", raw or "")
    if not match:
        return "0"
    index = int(match.group())
    if index < 1 or index > n_candidates:
        return "0"
    return str(index)


def evaluate_model(model_name: str, judge_llm_wrapper, cases: list[dict]) -> list[dict]:
    langchain_llm = judge_llm_wrapper.langchain_llm
    rows = []
    for i, case in enumerate(cases, start=1):
        prompt = build_prompt(case["chat"], case["candidates"])
        try:
            raw = call_model(langchain_llm, prompt)
        except Exception as e:
            print(f"  [{model_name}] {case['case_id']} 호출 실패: {e}")
            raw = ""
        choice = parse_choice(raw, len(case["candidates"]))
        rows.append({
            "case_id": case["case_id"],
            "chat": case["chat"],
            "reference": case["reference"],
            "model": model_name,
            "model_response": choice,
        })
        if i % 10 == 0:
            print(f"  [{model_name}] {i}/{len(cases)}건 진행")
        time.sleep(0.2)  # 과도한 동시요청/레이트리밋 방지용 최소 딜레이 (동시성 없이 순차 실행)
    return rows


def compute_metrics(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["exact_match"] = (df["model_response"] == df["reference"]).astype(float)
    accuracy = df["exact_match"].mean()

    df["actual_positive"] = df["reference"] != "0"
    df["predicted_positive"] = df["model_response"] != "0"
    tp = int((df["actual_positive"] & df["predicted_positive"]).sum())
    fp = int((~df["actual_positive"] & df["predicted_positive"]).sum())
    fn = int((df["actual_positive"] & ~df["predicted_positive"]).sum())
    tn = int((~df["actual_positive"] & ~df["predicted_positive"]).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "n": len(df), "accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def main():
    cases = load_cases(SELECTION_CASES_PATH)
    cases = [c for c in cases if c.get("reference") is not None]
    if not cases:
        print("[오류] reference가 채워진 케이스가 없습니다. situation_selection_cases.json을 먼저 채워주세요.")
        return

    all_rows = []
    summaries = {}
    for model_name, build_judge in JUDGES.items():
        print(f"\n[선택 작업 재실행] model={model_name} ({len(cases)}건)")
        try:
            judge_llm_wrapper = build_judge()
        except Exception as e:
            print(f"  [건너뜀] {model_name} 연결 실패: {e}")
            continue
        rows = evaluate_model(model_name, judge_llm_wrapper, cases)
        all_rows.extend(rows)
        summaries[model_name] = compute_metrics(pd.DataFrame(rows))
        m = summaries[model_name]
        print(
            f"  -> Accuracy={m['accuracy']:.3f} Precision={m['precision']:.3f} "
            f"Recall={m['recall']:.3f} F1={m['f1']:.3f}"
        )

    if not all_rows:
        print("[오류] 4개 모델 모두 연결에 실패했습니다. 위 로그를 확인하세요.")
        return

    combined = pd.DataFrame(all_rows)
    out_path = RESULTS_DIR / "1b_selection_by_model_result.csv"
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n  -> {out_path}")

    summary_path = RESULTS_DIR / "1b_selection_by_model_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    print(f"  -> {summary_path}")

    print("\n[모델별 요약]")
    print(pd.DataFrame(summaries).T[["n", "accuracy", "precision", "recall", "f1"]])


if __name__ == "__main__":
    main()
