# 정책 문서 임베딩 코드(search_text만, 전체 다) - bge_m3 임베딩 모델

import json
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


INPUT_FILE = "result/search_docs_watsonx_cleaned.json"
OUTPUT_DIR = "embeddings_search_docs"

MODEL_NAME = "BAAI/bge-m3"
MODEL_KEY = "bge_m3"

BATCH_SIZE = 64


def load_docs(path):
    """검색문서 JSON 파일을 읽는다."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_policy_text(doc, mode):
    """검색문서 하나를 임베딩할 텍스트로 만든다. "search_text_only"는 검색문서 필드만,
    "full_text"는 정책명/요약/대상/지원내용 등을 다 합친 텍스트를 만든다."""
    if mode == "search_text_only":
        return doc["search_text"]

    elif mode == "full_text":
        return f"""
정책명: {doc["policy_name"]}
요약: {doc["summary"]}
대상: {", ".join(doc["target"])}
지원내용: {", ".join(doc["support"])}
키워드: {", ".join(doc["keywords"])}
상황: {", ".join(doc["situations"])}
검색문서: {doc["search_text"]}
""".strip()

    raise ValueError(mode)


def save_json(path, data):
    """데이터를 JSON 파일로 저장한다(폴더가 없으면 만든다)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_embeddings(docs, model, mode):
    """검색문서 전체를 지정된 모드(search_text_only/full_text)로 임베딩하고,
    임베딩 배열과 정책 id/이름/원문 텍스트를 파일로 저장한다."""
    output_dir = Path(OUTPUT_DIR) / MODEL_KEY / mode
    output_dir.mkdir(parents=True, exist_ok=True)

    texts = [build_policy_text(doc, mode) for doc in docs]
    ids = [doc["policy_id"] for doc in docs]
    names = [doc["policy_name"] for doc in docs]

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    np.save(output_dir / "policy_embeddings.npy", embeddings)
    save_json(output_dir / "policy_ids.json", ids)
    save_json(output_dir / "policy_names.json", names)
    save_json(output_dir / "policy_texts.json", texts)

    print(f"\n[{mode}]")
    print("shape:", embeddings.shape)
    print("saved:", output_dir)


def main():
    """정제된 검색문서를 두 가지 모드(search_text_only/full_text)로 각각 임베딩해서 저장한다."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 50)
    print("Device :", device)

    if device == "cuda":
        print("GPU :", torch.cuda.get_device_name(0))

    print("=" * 50)

    docs = load_docs(INPUT_FILE)

    model = SentenceTransformer(
        MODEL_NAME,
        device=device,
    )

    build_embeddings(docs, model, "search_text_only")
    build_embeddings(docs, model, "full_text")


if __name__ == "__main__":
    main()