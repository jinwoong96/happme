"""
Ragas로 상황매칭 LLM(recommendation_service.py) 평가하는 스크립트.

대상 (2개, 성격이 달라서 서로 다른 지표를 씀)
1. _llm_select_candidate — 유사도 top10 후보 중 상황에 맞는 1개 선택(없으면 0)
   -> ExactMatch (judge LLM 필요 없음, 정답 번호와 그냥 문자열 비교)
2. _llm_explain_policy — 선택된 정책 상세정보(context)를 근거로 추천 이유 생성
   -> Faithfulness + ResponseRelevancy (judge LLM 4개로 비교, 아래 JUDGES 참고)

judge 모델 4개 (2번 평가에만 쓰임)
- watsonx_mistral_small_24b : mistralai/mistral-small-3-1-24b-instruct-2503
  (지금 recommendation_service.py가 실제로 답변 생성에 쓰는 모델과 동일 -> self-eval 기준선)
- watsonx_llama_3_3_70b     : meta-llama/llama-3-3-70b-instruct (같은 watsonx, 더 큰 모델)
- ollama_qwen3_8b           : qwen3:8b (로컬, 무료. 원래 qwen2.5:32b-instruct로 계획했으나
  로컬 하드웨어 부담 때문에 이미 pull해둔 qwen3:8b로 변경함)
- groq_llama_3_3_70b        : llama-3.3-70b-versatile (무료 클라우드, 카드 등록 불필요)

사전 준비 (전부 로컬 VS Code 환경에서)
    pip install -r requirements-eval.txt
    ollama pull qwen3:8b                      # Ollama 앱 설치 후
    # .env에 GROQ_API_KEY=... 추가 (console.groq.com 무료 가입)
    # watsonx 키는 bene_ai/.env에 이미 있음 (WATSONX_URL/WATSONX_API_KEY/WATSONX_PROJECT_ID)

테스트 데이터 (아직 비어있음 - TODO: 정답셋 채우기)
    test_cases/situation_selection_cases.json  <- 1번 평가용, 스키마는 situation_selection_example.json 참고
    test_cases/situation_explain_cases.json    <- 2번 평가용, 스키마는 situation_explain_example.json 참고
    두 파일 다 지금은 빈 배열([])이라, 이대로 실행하면 "테스트 케이스 없음" 경고만 찍히고 끝난다.

실행
    python ragas_eval.py
"""

import asyncio
import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from ragas import evaluate
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
from ragas.metrics import ExactMatch, Faithfulness, ResponseRelevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.run_config import RunConfig

# ragas 기본값(동시요청 16개, 짧은 타임아웃)은 watsonx 레이트리밋/로컬 Ollama 병목에서
# TimeoutError가 대량 발생함. 동시요청을 확 줄이고 타임아웃을 넉넉히 잡아서 재시도로
# 커버하도록 완화한다. 느려지는 대신 결과 누락(NaN)을 줄이는 게 목적.
EVAL_RUN_CONFIG = RunConfig(timeout=300, max_retries=3, max_wait=60, max_workers=3)

load_dotenv()

BASE_DIR = Path(__file__).parent
CASES_DIR = BASE_DIR / "test_cases"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

SELECTION_CASES_PATH = CASES_DIR / "situation_selection_cases.json"
EXPLAIN_CASES_PATH = CASES_DIR / "situation_explain_cases.json"

# ResponseRelevancy는 LLM뿐 아니라 임베딩 모델도 필요하다(생성된 답변에서 역으로 질문을
# 만들어 원 질문과의 코사인 유사도를 봄). similarity_search.py가 이미 쓰고 있는 모델을
# 그대로 재사용해서 평가용 임베딩과 서비스용 임베딩을 다르게 두지 않았다.
EVAL_EMBED_MODEL = "BAAI/bge-m3"


def _load_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings

    return LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=EVAL_EMBED_MODEL))


# ---------- judge 모델 4개 ----------

def build_watsonx_judge(model_id: str) -> LangchainLLMWrapper:
    """watsonx 모델을 Ragas judge로 감싼다. bene_ai/.env의 기존 watsonx 키를 그대로 재사용한다."""
    from langchain_ibm import WatsonxLLM

    llm = WatsonxLLM(
        model_id=model_id,
        url=os.getenv("WATSONX_URL"),
        apikey=os.getenv("WATSONX_API_KEY"),
        project_id=os.getenv("WATSONX_PROJECT_ID"),
        params={"temperature": 0, "max_new_tokens": 500},
    )
    return LangchainLLMWrapper(llm)


def build_ollama_judge(model_tag: str = "qwen3:8b") -> LangchainLLMWrapper:
    """로컬 Ollama 모델을 Ragas judge로 감싼다. 사전에 `ollama pull {model_tag}`가 필요하고,
    Ollama 앱(서버)이 로컬에서 떠 있어야 한다."""
    from langchain_ollama import ChatOllama

    llm = ChatOllama(model=model_tag, temperature=0)
    return LangchainLLMWrapper(llm)


def build_groq_judge(model_id: str = "llama-3.3-70b-versatile") -> LangchainLLMWrapper:
    """Groq 무료 API를 Ragas judge로 감싼다. .env에 GROQ_API_KEY가 있어야 한다."""
    from langchain_groq import ChatGroq

    llm = ChatGroq(model=model_id, api_key=os.getenv("GROQ_API_KEY"), temperature=0)
    return LangchainLLMWrapper(llm)


# 함수를 바로 실행하지 않고 lambda로 감싸둔 이유: 4개 다 매번 만들면 느리므로(특히 Ollama/watsonx
# 연결), evaluate_explanation()에서 judge 하나씩 필요할 때만 만든다.
JUDGES = {
    "watsonx_mistral_small_24b": lambda: build_watsonx_judge("mistralai/mistral-small-3-1-24b-instruct-2503"),
    "watsonx_llama_3_3_70b": lambda: build_watsonx_judge("meta-llama/llama-3-3-70b-instruct"),
    "ollama_qwen3_8b": lambda: build_ollama_judge("qwen3:8b"),
    "groq_llama_3_3_70b": lambda: build_groq_judge("llama-3.3-70b-versatile"),
}


# ---------- 공용 ----------

def load_cases(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        print(f"[경고] 테스트 케이스 파일이 비어있거나 없습니다: {path}")
        return []
    with open(path, encoding="utf-8") as f:
        cases = json.load(f)
    if not cases:
        print(f"[경고] 테스트 케이스가 0건입니다: {path} (정답셋을 아직 안 채우셨다면 정상입니다)")
    return cases


# ---------- 1) _llm_select_candidate 평가 (ExactMatch, judge LLM 불필요) ----------
# 정답이 하나로 정해진 선택형 분류라 LLM 심사가 필요 없다. judge 모델을 바꿔도 결과가
# 달라지지 않으므로(항상 같은 결정론적 비교), 여기서는 4개 judge 비교를 하지 않는다.

async def evaluate_selection() -> pd.DataFrame:
    """case 스키마: {"case_id", "chat", "candidates": [...], "llm_response": "3", "reference": "3"}
    llm_response/reference는 candidates의 1-base 번호 문자열, 없으면 "0"."""
    cases = load_cases(SELECTION_CASES_PATH)
    if not cases:
        return pd.DataFrame()

    unlabeled = [c for c in cases if c.get("reference") is None]
    if unlabeled:
        print(
            f"[경고] reference가 아직 null인 케이스 {len(unlabeled)}건은 건너뜁니다 "
            f"(case_id: {[c.get('case_id') for c in unlabeled]})"
        )
    cases = [c for c in cases if c.get("reference") is not None]
    if not cases:
        print("[오류] reference가 채워진 케이스가 하나도 없습니다.")
        return pd.DataFrame()

    scorer = ExactMatch()
    rows = []
    for case in cases:
        sample = SingleTurnSample(
            response=str(case["llm_response"]),
            reference=str(case["reference"]),
        )
        score = await scorer.single_turn_ascore(sample)
        rows.append({**case, "exact_match": score})

    df = pd.DataFrame(rows)
    accuracy = df["exact_match"].mean()

    # "정확히 몇 번을 골랐나"(accuracy)와 별개로, "애초에 정책이 있다/없다를 제대로
    # 감지했나"를 이진 탐지 문제로 다시 봐서 Precision/Recall/F1을 낸다.
    # positive(양성) = 이 상황에 맞는 정책이 실제로/LLM 판단상 있다(번호가 "0"이 아님)
    #   TP: 실제로 있고, LLM도 있다고 답함 (번호가 정확히 맞았는지는 별개 - accuracy가 그걸 봄)
    #   FP: 실제로는 없는데(reference="0") LLM이 있다고 답함 (할루시네이션)
    #   FN: 실제로는 있는데(reference!="0") LLM이 없다고 답함 (기회 손실)
    #   TN: 실제로도 없고 LLM도 없다고 답함
    df["actual_positive"] = df["reference"] != "0"
    df["predicted_positive"] = df["llm_response"].astype(str) != "0"
    tp = int(((df["actual_positive"]) & (df["predicted_positive"])).sum())
    fp = int((~df["actual_positive"] & df["predicted_positive"]).sum())
    fn = int((df["actual_positive"] & ~df["predicted_positive"]).sum())
    tn = int((~df["actual_positive"] & ~df["predicted_positive"]).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    print(f"\n[1. 선택형 분류] Accuracy(번호까지 정확히 일치): {accuracy:.3f}  ({len(df)}건)")
    print(
        f"[1. 존재 탐지(있음/없음)] Precision: {precision:.3f}  Recall: {recall:.3f}  "
        f"F1: {f1:.3f}  (TP={tp}, FP={fp}, FN={fn}, TN={tn})"
    )

    out_path = RESULTS_DIR / "1_selection_result.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  -> {out_path}")

    summary_path = RESULTS_DIR / "1_selection_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "n": len(df),
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            },
            f, ensure_ascii=False, indent=2,
        )
    print(f"  -> {summary_path}")
    return df


# ---------- 2) _llm_explain_policy 평가 (Faithfulness + ResponseRelevancy, judge 4개 비교) ----------

async def evaluate_explanation() -> pd.DataFrame:
    """case 스키마: {"case_id", "chat", "context", "llm_response"}
    - chat: 사용자 상황 (user_input)
    - context: 프롬프트에 넣었던 정책 상세정보 텍스트 (retrieved_contexts)
    - llm_response: _llm_explain_policy가 실제로 생성한 답변 (response)
    judge 4개 각각으로 전체 케이스를 채점해서 judge별 평균을 비교한다."""
    cases = load_cases(EXPLAIN_CASES_PATH)
    if not cases:
        return pd.DataFrame()

    samples = [
        SingleTurnSample(
            user_input=case["chat"],
            response=case["llm_response"],
            retrieved_contexts=[case["context"]],
        )
        for case in cases
    ]
    dataset = EvaluationDataset(samples=samples)
    embeddings = _load_embeddings()

    all_results = []
    for judge_name, build_judge in JUDGES.items():
        print(f"\n[2. 근거기반생성] judge={judge_name} 평가 중... ({len(cases)}건)")
        try:
            judge_llm = build_judge()
        except Exception as e:
            print(f"  [건너뜀] {judge_name} 연결 실패: {e}")
            continue

        result = evaluate(
            dataset,
            metrics=[
                Faithfulness(llm=judge_llm),
                ResponseRelevancy(llm=judge_llm, embeddings=embeddings),
            ],
            run_config=EVAL_RUN_CONFIG,
        )
        result_df = result.to_pandas()
        # NOTE: 컬럼명이 사용 중인 ragas 버전에 따라 answer_relevancy로 나올 수도 있음.
        # 실행 후 result_df.columns로 실제 컬럼명 확인.
        result_df["judge"] = judge_name
        for case, (_, row) in zip(cases, result_df.iterrows()):
            result_df.loc[_, "case_id"] = case.get("case_id")
        all_results.append(result_df)

    if not all_results:
        print("[오류] 4개 judge 모두 연결에 실패했습니다. 위 로그를 확인하세요.")
        return pd.DataFrame()

    combined = pd.concat(all_results, ignore_index=True)

    out_path = RESULTS_DIR / "2_explanation_result.csv"
    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n  -> {out_path}")

    score_cols = [c for c in combined.columns if c in ("faithfulness", "answer_relevancy", "response_relevancy")]
    summary = combined.groupby("judge")[score_cols].mean()
    print("\n[2. 근거기반생성] judge별 평균 점수")
    print(summary)
    return combined


async def main():
    await evaluate_selection()
    await evaluate_explanation()


if __name__ == "__main__":
    asyncio.run(main())
