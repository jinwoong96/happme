from app.core.settings import settings
from app.core.s3_utils import get_s3_client, download_if_missing_or_stale


def ensure_data_downloaded() -> None:
    """정책 원본 JSON/정적 임베딩/사전 계산 캐시를 S3와 비교해서 로컬에 없거나 S3 쪽이 더
    최신이면 내려받습니다. 재계산 가능한 캐시(policy_embedding_cache, policy_summary_embed_cache)는
    원본 데이터가 더 최신이라 로컬 재계산이 일어나면 각 서비스가 직접 S3에 다시 업로드합니다."""
    if not settings.data_s3_bucket:
        print("[data_downloader] DATA_S3_BUCKET이 비어있어 다운로드를 건너뜁니다 (로컬 파일 사용).")
        return

    client = get_s3_client(settings.data_s3_public)
    bucket = settings.data_s3_bucket

    for local_path, s3_key in (
        (settings.policy_list_path, settings.policy_list_s3_key),
        (settings.zipcd_mapping_path, settings.zipcd_mapping_s3_key),
        (settings.similarity_docs_path, settings.similarity_docs_s3_key),
        (settings.similarity_embeddings_path, settings.similarity_embeddings_s3_key),
        (settings.policy_embedding_cache, settings.policy_embedding_cache_s3_key),
        (settings.policy_summary_embed_cache, settings.policy_summary_embed_cache_s3_key),
    ):
        download_if_missing_or_stale(local_path, bucket, s3_key, client, label="data_downloader")
