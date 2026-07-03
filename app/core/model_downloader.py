import os

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.settings import settings


def _get_s3_client():
    if settings.model_s3_public:
        return boto3.client("s3", config=Config(signature_version=UNSIGNED))
    return boto3.client("s3")


def _download_if_missing(local_path: str, s3_key: str, client) -> None:
    if not s3_key:
        print(f"[model_downloader] S3 key가 설정되지 않아 건너뜁니다: {local_path}")
        return

    if os.path.exists(local_path):
        print(f"[model_downloader] 이미 존재하여 건너뜀: {local_path}")
        return

    local_dir = os.path.dirname(local_path)
    if local_dir:
        os.makedirs(local_dir, exist_ok=True)

    print(f"[model_downloader] 다운로드 중: s3://{settings.model_s3_bucket}/{s3_key} -> {local_path}")
    try:
        client.download_file(settings.model_s3_bucket, s3_key, local_path)
    except NoCredentialsError as e:
        raise RuntimeError(
            "AWS 자격증명을 찾을 수 없습니다. 'aws configure'로 등록하거나, "
            "퍼블릭 버킷이라면 .env의 MODEL_S3_PUBLIC=true로 설정하세요."
        ) from e
    except ClientError as e:
        raise RuntimeError(
            f"S3 다운로드 실패 (bucket={settings.model_s3_bucket}, key={s3_key}): {e}"
        ) from e

    print(f"[model_downloader] 완료: {local_path}")


def ensure_models_downloaded() -> None:
    """필요한 모델 가중치가 로컬에 없으면 S3에서 내려받습니다."""
    if not settings.model_s3_bucket:
        print("[model_downloader] MODEL_S3_BUCKET이 비어있어 다운로드를 건너뜁니다 (로컬 파일 사용).")
        return

    client = _get_s3_client()
    _download_if_missing(settings.notice_detector_weights, settings.notice_detector_s3_key, client)
    _download_if_missing(settings.text_region_detector_weights, settings.text_region_detector_s3_key, client)