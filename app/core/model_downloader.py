from app.core.settings import settings
from app.core.s3_utils import get_s3_client, download_if_missing


def ensure_models_downloaded() -> None:
    """필요한 모델 가중치가 로컬에 없으면 S3에서 내려받습니다."""
    if not settings.model_s3_bucket:
        print("[model_downloader] MODEL_S3_BUCKET이 비어있어 다운로드를 건너뜁니다 (로컬 파일 사용).")
        return

    client = get_s3_client(settings.model_s3_public)
    download_if_missing(
        settings.notice_detector_weights, settings.model_s3_bucket, settings.notice_detector_s3_key,
        client, label="model_downloader",
    )
    download_if_missing(
        settings.text_region_detector_weights, settings.model_s3_bucket, settings.text_region_detector_s3_key,
        client, label="model_downloader",
    )
