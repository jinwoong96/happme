"""
judge 4개(watsonx x2, Ollama, Groq)가 실제로 연결되는지 미리 확인하는 스모크 테스트.
ragas_eval.py를 본격적으로 돌리기 전에, 각 judge에 "1"이라고만 답하게 시켜보고
성공/실패만 빠르게 확인한다. (ragas 설치 없이도 이 스크립트만 따로 돌릴 수 있음)

사전 준비
    pip install langchain-ibm langchain-ollama langchain-groq python-dotenv
    (requirements-eval.txt를 이미 설치했다면 이 4개는 포함돼 있음)

실행 (로컬에서, 이 파일이 있는 evaluation 폴더 기준)
    python check_judges.py
"""

import os

from dotenv import load_dotenv

load_dotenv()

TEST_PROMPT = "숫자 1만 답하세요. 다른 말은 하지 마세요."


def check_watsonx(model_id: str) -> None:
    from langchain_ibm import WatsonxLLM

    llm = WatsonxLLM(
        model_id=model_id,
        url=os.getenv("WATSONX_URL"),
        apikey=os.getenv("WATSONX_API_KEY"),
        project_id=os.getenv("WATSONX_PROJECT_ID"),
        params={"temperature": 0, "max_new_tokens": 20},
    )
    result = llm.invoke(TEST_PROMPT)
    print(f"  응답: {result!r}")


def check_ollama(model_tag: str = "qwen3:8b") -> None:
    from langchain_ollama import ChatOllama

    llm = ChatOllama(model=model_tag, temperature=0)
    result = llm.invoke(TEST_PROMPT)
    print(f"  응답: {result.content!r}")


def check_groq(model_id: str = "llama-3.3-70b-versatile") -> None:
    from langchain_groq import ChatGroq

    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError(".env에 GROQ_API_KEY가 없습니다.")
    llm = ChatGroq(model=model_id, api_key=key, temperature=0)
    result = llm.invoke(TEST_PROMPT)
    print(f"  응답: {result.content!r}")


CHECKS = {
    "watsonx_mistral_small_24b": lambda: check_watsonx("mistralai/mistral-small-3-1-24b-instruct-2503"),
    "watsonx_llama_3_3_70b": lambda: check_watsonx("meta-llama/llama-3-3-70b-instruct"),
    "ollama_qwen3_8b": lambda: check_ollama("qwen3:8b"),
    "groq_llama_3_3_70b": lambda: check_groq("llama-3.3-70b-versatile"),
}


def main():
    results = {}
    for name, check_fn in CHECKS.items():
        print(f"\n[{name}] 확인 중...")
        try:
            check_fn()
            results[name] = "OK"
        except Exception as e:
            print(f"  실패: {type(e).__name__}: {e}")
            results[name] = "FAIL"

    print("\n" + "=" * 40)
    print("결과 요약")
    print("=" * 40)
    for name, status in results.items():
        mark = "✅" if status == "OK" else "❌"
        print(f"{mark} {name}: {status}")


if __name__ == "__main__":
    main()
