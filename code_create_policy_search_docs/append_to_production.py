# 독립 프로세스로 만든 검색문서(정제 완료)를 운영 파일에 이어붙이기
#
# run_create_search_docs.py -> clean_search_docs.py까지 돌려서 나온
# result/search_docs_watsonx_cleaned.json을, 실제 서비스가 쓰는 운영 파일
# (data/policy_search_docs.json, data/embeddings/search_docs_full_text_embeddings.npy)에
# 이어붙인다. 이미 운영 파일에 있는 policy_id는 건너뛰어서, 여러 번 실행해도 중복 추가되지 않는다.
#
# 실행 위치: ai/ (다른 파이프라인 스크립트들과 동일)
# 사용법: python -m code_create_policy_search_docs.append_to_production

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.settings import settings
from app.core.s3_utils import get_s3_client, upload_file
from code_create_policy_search_docs.build_search_doc_embeddings import build_policy_text

INPUT_FILE = "result/search_docs_watsonx_cleaned.json"


def load_json(path, default=None):
    """JSON 파일을 읽는다. 파일이 없으면 default(기본값은 빈 리스트)를 반환한다."""
    p = Path(path)
    if not p.exists():
        return default if default is not None else []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """데이터를 JSON 파일로 저장한다(폴더가 없으면 만든다)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def upload_if_configured(local_path: str, s3_key: str) -> None:
    """S3 설정이 돼 있으면 파일을 업로드하고, 아니면 아무것도 하지 않는다."""
    if settings.data_s3_bucket and s3_key:
        client = get_s3_client(settings.data_s3_public)
        upload_file(local_path, settings.data_s3_bucket, s3_key, client, label="append_to_production")


def main():
    """정제된 신규 검색문서 중 운영 파일에 아직 없는 것만 임베딩해서 이어붙이고 저장한다."""
    new_docs = load_json(INPUT_FILE)
    if not new_docs:
        print(f"{INPUT_FILE}에 문서가 없습니다. 종료합니다.")
        return

    existing_docs = load_json(settings.similarity_docs_path)
    existing_ids = {str(d.get("policy_id")) for d in existing_docs}

    # 이미 운영 파일에 있는 건 건너뛴다 (여러 번 실행해도 안전하도록).
    docs_to_add = [d for d in new_docs if str(d.get("policy_id")) not in existing_ids]

    print(f"입력 문서 수: {len(new_docs)}")
    print(f"이미 운영 파일에 있어 건너뜀: {len(new_docs) - len(docs_to_add)}")
    print(f"새로 추가할 문서 수: {len(docs_to_add)}")

    if not docs_to_add:
        print("추가할 문서가 없습니다. 종료합니다.")
        return

    print(f"임베딩 모델 로드 중... ({settings.similarity_model_name})")
    model = SentenceTransformer(settings.similarity_model_name)

    texts = [build_policy_text(doc, "full_text") for doc in docs_to_add]
    new_embeddings = model.encode(
        texts, batch_size=64, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True,
    )

    embeddings_path = Path(settings.similarity_embeddings_path)
    existing_embeddings = np.load(embeddings_path) if embeddings_path.exists() else None

    combined_docs = existing_docs + docs_to_add
    combined_embeddings = (
        np.vstack([existing_embeddings, new_embeddings]) if existing_embeddings is not None else new_embeddings
    )

    save_json(settings.similarity_docs_path, combined_docs)
    np.save(settings.similarity_embeddings_path, combined_embeddings)

    print(f"저장 완료: {settings.similarity_docs_path} ({len(combined_docs)}건)")
    print(f"저장 완료: {settings.similarity_embeddings_path} (shape={combined_embeddings.shape})")

    upload_if_configured(settings.similarity_docs_path, settings.similarity_docs_s3_key)
    upload_if_configured(settings.similarity_embeddings_path, settings.similarity_embeddings_s3_key)


if __name__ == "__main__":
    main()
