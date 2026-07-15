import os

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError


def get_s3_client(public: bool):
    if public:
        return boto3.client("s3", config=Config(signature_version=UNSIGNED))
    return boto3.client("s3")


def download_if_missing(local_path: str, bucket: str, s3_key: str, client, label: str = "s3_utils") -> None:
    if not s3_key:
        print(f"[{label}] S3 key가 설정되지 않아 건너뜁니다: {local_path}")
        return

    if os.path.exists(local_path):
        print(f"[{label}] 이미 존재하여 건너뜀: {local_path}")
        return

    local_dir = os.path.dirname(local_path)
    if local_dir:
        os.makedirs(local_dir, exist_ok=True)

    print(f"[{label}] 다운로드 중: s3://{bucket}/{s3_key} -> {local_path}")
    try:
        client.download_file(bucket, s3_key, local_path)
    except NoCredentialsError as e:
        raise RuntimeError(
            "AWS 자격증명을 찾을 수 없습니다. 'aws configure'로 등록하거나, "
            "퍼블릭 버킷이라면 .env의 *_S3_PUBLIC=true로 설정하세요."
        ) from e
    except ClientError as e:
        raise RuntimeError(f"S3 다운로드 실패 (bucket={bucket}, key={s3_key}): {e}") from e

    print(f"[{label}] 완료: {local_path}")


def upload_file(local_path: str, bucket: str, s3_key: str, client, label: str = "s3_utils") -> None:
    """재계산된 캐시 파일을 S3에 다시 올린다. 실패해도 로컬 캐시로는 계속 동작해야 하므로 예외를 던지지 않고 로그만 남긴다."""
    if not bucket or not s3_key:
        return
    try:
        print(f"[{label}] 업로드 중: {local_path} -> s3://{bucket}/{s3_key}")
        client.upload_file(local_path, bucket, s3_key)
        print(f"[{label}] 업로드 완료: s3://{bucket}/{s3_key}")
    except (ClientError, NoCredentialsError) as e:
        print(f"[{label}] S3 업로드 실패(로컬 캐시로 계속 진행): {e}")
