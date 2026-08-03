"""
evaluation/results/*.csv 결과를 보여주는 Streamlit 대시보드. 뷰어 전용이라 ragas_eval.py를
포함한 기존 코드는 전혀 건드리지 않고, 결과 파일만 읽는다.

실행법
    pip install -r requirements-eval.txt   # streamlit 포함됨
    streamlit run dashboard.py

아직 python ragas_eval.py를 실행하지 않아서 results/ 폴더가 비어있어도, 화면 구성을
미리 볼 수 있도록 예시(더미) 데이터로 대체해서 보여준다("더미 데이터" 배너로 표시됨).
실제 결과 파일(results/1_selection_result.csv 등)이 생기면 자동으로 그걸 우선 사용한다.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"

SELECTION_CSV = RESULTS_DIR / "1_selection_result.csv"
SELECTION_SUMMARY = RESULTS_DIR / "1_selection_summary.json"
EXPLANATION_CSV = RESULTS_DIR / "2_explanation_result.csv"
SELECTION_BY_MODEL_CSV = RESULTS_DIR / "1b_selection_by_model_result.csv"
SELECTION_BY_MODEL_SUMMARY = RESULTS_DIR / "1b_selection_by_model_summary.json"

st.set_page_config(page_title="상황매칭 LLM 성능평가", layout="wide")


# ---------- 더미 데이터 (results/ 파일이 없을 때 화면 미리보기용) ----------

def _dummy_selection() -> tuple[pd.DataFrame, dict]:
    summary = {"n": 8, "accuracy": 0.625, "precision": 0.83, "recall": 0.71, "f1": 0.77,
               "tp": 5, "fp": 1, "fn": 2, "tn": 0}
    df = pd.DataFrame([
        {"case_id": "sel_001", "chat": "생활비 지원 정책 찾는 중", "llm_response": "0", "reference": "0", "exact_match": 1.0},
        {"case_id": "sel_002", "chat": "학자금 대출 이자 부담", "llm_response": "3", "reference": "0", "exact_match": 0.0},
        {"case_id": "sel_003", "chat": "마음이 힘들어서 상담", "llm_response": "1", "reference": "1", "exact_match": 1.0},
        {"case_id": "sel_007", "chat": "복직 준비, 아이돌봄 지원", "llm_response": "1", "reference": "0", "exact_match": 0.0},
    ])
    return df, summary


def _dummy_explanation() -> pd.DataFrame:
    judges = ["watsonx_mistral_small_24b", "watsonx_llama_3_3_70b", "ollama_qwen3_8b", "groq_llama_3_3_70b"]
    base_scores = {
        "watsonx_mistral_small_24b": (0.82, 0.78),
        "watsonx_llama_3_3_70b": (0.88, 0.84),
        "ollama_qwen3_8b": (0.74, 0.70),
        "groq_llama_3_3_70b": (0.86, 0.81),
    }
    rows = []
    for i in range(1, 7):
        for j in judges:
            f, r = base_scores[j]
            rows.append({
                "case_id": f"exp_{i:03d}",
                "judge": j,
                "faithfulness": round(min(f + (i % 3) * 0.02, 1.0), 3),
                "answer_relevancy": round(min(r + (i % 2) * 0.03, 1.0), 3),
            })
    return pd.DataFrame(rows)


# ---------- 데이터 로드 (실제 결과 우선, 없으면 더미) ----------

@st.cache_data
def load_selection() -> tuple[pd.DataFrame, dict, bool]:
    if SELECTION_CSV.exists() and SELECTION_SUMMARY.exists():
        df = pd.read_csv(SELECTION_CSV)
        with open(SELECTION_SUMMARY, encoding="utf-8") as f:
            summary = json.load(f)
        return df, summary, False
    df, summary = _dummy_selection()
    return df, summary, True


@st.cache_data
def load_explanation() -> tuple[pd.DataFrame, bool]:
    if EXPLANATION_CSV.exists():
        return pd.read_csv(EXPLANATION_CSV), False
    return _dummy_explanation(), True


@st.cache_data
def load_selection_by_model() -> tuple[pd.DataFrame, dict, bool]:
    """evaluate_selection_models.py 결과: 프로덕션 모델뿐 아니라 4개 모델이 각각
    선택 작업(_llm_select_candidate)을 직접 수행했을 때의 Accuracy/P/R/F1 비교."""
    if SELECTION_BY_MODEL_CSV.exists() and SELECTION_BY_MODEL_SUMMARY.exists():
        df = pd.read_csv(SELECTION_BY_MODEL_CSV)
        with open(SELECTION_BY_MODEL_SUMMARY, encoding="utf-8") as f:
            summary = json.load(f)
        return df, summary, False
    return pd.DataFrame(), {}, True


# ---------- 화면 ----------

st.title("상황매칭 LLM 성능평가")
st.caption("recommendation_service.py의 _llm_select_candidate(1.1) / _llm_explain_policy(1.2) 평가 결과")

sel_df, sel_summary, sel_is_dummy = load_selection()
exp_df, exp_is_dummy = load_explanation()
sel_by_model_df, sel_by_model_summary, sel_by_model_missing = load_selection_by_model()

if sel_is_dummy or exp_is_dummy:
    st.warning(
        "아직 `python ragas_eval.py`를 실행하지 않아서 예시(더미) 데이터로 화면을 보여주고 있어요. "
        "`results/` 폴더에 실제 결과가 생기면 새로고침 시 자동으로 실제 데이터로 바뀝니다.",
        icon="⚠️",
    )

tab1, tab2 = st.tabs(["1. 선택형 분류 (_llm_select_candidate)", "2. 근거기반생성 (_llm_explain_policy)"])

# ---------- 탭 1: 선택형 분류 (Accuracy / Precision / Recall / F1) ----------
with tab1:
    st.subheader("존재 탐지(있음/없음) 지표")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("케이스 수", sel_summary["n"])
    c2.metric("Accuracy(번호까지 일치)", f"{sel_summary['accuracy']:.1%}")
    c3.metric("Precision", f"{sel_summary['precision']:.1%}")
    c4.metric("Recall", f"{sel_summary['recall']:.1%}")
    c5.metric("F1", f"{sel_summary['f1']:.1%}")
    st.caption(
        f"TP(정확히 감지)={sel_summary['tp']}  FP(할루시네이션)={sel_summary['fp']}  "
        f"FN(기회 손실)={sel_summary['fn']}  TN(정상적으로 없음)={sel_summary['tn']}"
    )

    st.divider()
    st.subheader("케이스별 상세")
    only_wrong = st.checkbox("오답만 보기 (exact_match = 0)", value=False)
    view_df = sel_df if not only_wrong else sel_df[sel_df["exact_match"] < 1]
    st.dataframe(view_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("모델별 비교 (4개 모델이 직접 선택 작업을 수행했을 때)")
    st.caption(
        "위 지표는 프로덕션 모델(watsonx mistral-small-24b) 답변 1개만 정답과 비교한 것. "
        "아래는 evaluate_selection_models.py로 4개 모델(watsonx mistral-24b/llama-70b, "
        "Ollama qwen3, Groq llama-70b) 각각에 동일한 프롬프트로 선택 작업을 다시 시킨 결과."
    )
    if sel_by_model_missing:
        st.info(
            "아직 `python evaluate_selection_models.py`를 실행하지 않아서 모델별 비교 결과가 없어요. "
            "실행 후 `results/1b_selection_by_model_result.csv`가 생기면 여기 표시됩니다.",
            icon="ℹ️",
        )
    else:
        summary_rows = []
        for model_name, m in sel_by_model_summary.items():
            summary_rows.append({
                "model": model_name,
                "n": m["n"],
                "accuracy": m["accuracy"],
                "precision": m["precision"],
                "recall": m["recall"],
                "f1": m["f1"],
                "tp": m["tp"], "fp": m["fp"], "fn": m["fn"], "tn": m["tn"],
            })
        model_summary_df = pd.DataFrame(summary_rows).set_index("model")

        st.bar_chart(model_summary_df[["accuracy", "precision", "recall", "f1"]])
        st.dataframe(
            model_summary_df.style.format({
                "accuracy": "{:.1%}", "precision": "{:.1%}", "recall": "{:.1%}", "f1": "{:.1%}",
            }),
            use_container_width=True,
        )

        st.divider()
        st.subheader("모델별 케이스 상세 (필터)")
        models_available = sorted(sel_by_model_df["model"].unique())
        picked_models = st.multiselect("모델 선택", models_available, default=models_available, key="model_filter")
        only_wrong_model = st.checkbox("오답만 보기", value=False, key="only_wrong_model")
        filtered_model_df = sel_by_model_df[sel_by_model_df["model"].isin(picked_models)]
        if only_wrong_model:
            filtered_model_df = filtered_model_df[filtered_model_df["model_response"] != filtered_model_df["reference"]]
        st.dataframe(filtered_model_df, use_container_width=True, hide_index=True)

# ---------- 탭 2: 근거기반생성 (judge별 Faithfulness / Response Relevancy) ----------
with tab2:
    st.subheader("Judge별 평균 점수 비교")
    score_cols = [c for c in ["faithfulness", "answer_relevancy", "response_relevancy"] if c in exp_df.columns]

    if not score_cols or "judge" not in exp_df.columns:
        st.error("결과 파일에서 judge/점수 컬럼을 찾지 못했어요. results/2_explanation_result.csv의 컬럼명을 확인해주세요.")
    else:
        judge_summary = exp_df.groupby("judge")[score_cols].mean().round(3)
        st.bar_chart(judge_summary)
        st.dataframe(judge_summary, use_container_width=True)

        st.divider()
        st.subheader("케이스별 상세 (judge 필터)")
        judges_available = sorted(exp_df["judge"].unique())
        picked_judges = st.multiselect("judge 선택", judges_available, default=judges_available)
        filtered = exp_df[exp_df["judge"].isin(picked_judges)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("점수 낮은 케이스 찾기 (할루시네이션 의심)")
        if "faithfulness" in exp_df.columns:
            threshold = st.slider("faithfulness 기준선", 0.0, 1.0, 0.7, 0.05)
            low_df = exp_df[exp_df["faithfulness"] < threshold]
            st.write(f"{len(low_df)}건이 기준선({threshold}) 미만")
            st.dataframe(low_df, use_container_width=True, hide_index=True)
