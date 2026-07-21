import os
from datetime import datetime, timezone

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError


def get_s3_client(public: bool):
    if public:
        return boto3.client("s3", config=Config(signature_version=UNSIGNED))
    return boto3.client("s3")


def _is_s3_object_newer(local_path: str, bucket: str, s3_key: str, client, label: str) -> bool:
    """S3 객체의 LastModified가 로컬 파일 수정시각보다 최신이면 True.
    HEAD 요청 자체가 실패하면(권한/네트워크 문제) 굳이 재다운로드를 강제하지 않고 로컬
    파일을 그대로 쓰도록 False를 반환한다."""
    try:
        head = client.head_object(Bucket=bucket, Key=s3_key)
    except (ClientError, NoCredentialsError) as e:
        print(f"[{label}] S3 최신 여부 확인 실패, 로컬 파일을 그대로 사용합니다: {e}")
        return False

    s3_last_modified = head["LastModified"]
    local_mtime = datetime.fromtimestamp(os.path.getmtime(local_path), tz=timezone.utc)
    return s3_last_modified > local_mtime


def download_if_missing_or_stale(local_path: str, bucket: str, s3_key: str, client, label: str = "s3_utils") -> None:
    """로컬 파일이 없으면 무조건 받고, 있으면 S3의 LastModified와 로컬 수정시각을 비교해서
    S3 쪽이 더 최신일 때만 다시 받는다. 로컬 존재 여부만 보던 예전 방식은 다른 서버/배포가
    S3에 새 캐시를 올려도 이 서버가 영영 모르는 문제가 있었다."""
    if not s3_key:
        print(f"[{label}] S3 key가 설정되지 않아 건너뜁니다: {local_path}")
        return

    if os.path.exists(local_path):
        if not _is_s3_object_newer(local_path, bucket, s3_key, client, label):
            print(f"[{label}] 로컬 파일이 최신이라 건너뜀: {local_path}")
            return
        print(f"[{label}] S3에 더 최신 파일이 있어 다시 받습니다: {local_path}")

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
