"""
logs/ 아래 날짜별로 로테이션된 로그 파일(ai.log.YYYY-MM-DD, steps.jsonl.YYYY-MM-DD)을
S3에 업로드하고, 업로드된 게 확인된 파일만 로컬에서 지운다.
오늘 계속 쓰이고 있는 파일(ai.log, steps.jsonl - 날짜 접미사 없음)과 오늘 날짜로
막 로테이션된 파일은 건드리지 않는다.

사전 준비:
    .env에 DATA_S3_BUCKET (모델/데이터 캐시와 같은 버킷 재사용), 필요하면 LOG_S3_PREFIX 설정
    (기본값 "ai-storage/logs")

실행:
    python upload_logs_to_s3.py

매일 새벽 3시에 자동 실행하려면 EC2에 cron 등록 (venv 경로는 실제 환경에 맞게 수정):
    0 3 * * * cd /home/ubuntu/bene_ai && /home/ubuntu/bene_ai/venv/bin/python upload_logs_to_s3.py >> logs/upload_logs.log 2>&1
"""
import os
import re
from datetime import date

from botocore.exceptions import ClientError, NoCredentialsError

from app.core.settings import settings
from app.core.s3_utils import get_s3_client

DATE_SUFFIX_RE = re.compile(r"\.(\d{4}-\d{2}-\d{2})$")


def _iter_rotated_log_files(log_dir: str):
    """날짜 접미사가 붙은(=자정에 이미 로테이션이 끝난) 파일만, 그리고 오늘 날짜보다
    이전 파일만 골라낸다. 오늘 쓰이고 있는 파일(접미사 없음)과 오늘 막 로테이션된 파일은
    제외해서, 아직 쓰는 중인 파일을 건드리는 사고를 막는다."""
    today_str = date.today().isoformat()
    if not os.path.isdir(log_dir):
        return
    for name in sorted(os.listdir(log_dir)):
        m = DATE_SUFFIX_RE.search(name)
        if not m:
            continue
        file_date = m.group(1)
        if file_date >= today_str:
            continue
        yield name, file_date


def _upload_and_verify(local_path: str, bucket: str, s3_key: str, client) -> bool:
    try:
        client.upload_file(local_path, bucket, s3_key)
    except (ClientError, NoCredentialsError) as e:
        print(f"[upload_logs] 업로드 실패, 파일 유지: {local_path} ({e})")
        return False

    try:
        head = client.head_object(Bucket=bucket, Key=s3_key)
    except (ClientError, NoCredentialsError) as e:
        print(f"[upload_logs] 업로드 확인 실패, 삭제 보류: {local_path} ({e})")
        return False

    if head["ContentLength"] != os.path.getsize(local_path):
        print(f"[upload_logs] 업로드 후 크기 불일치, 삭제 보류: {local_path}")
        return False

    return True


def main():
    if not settings.data_s3_bucket:
        print("[upload_logs] DATA_S3_BUCKET이 비어있어 건너뜁니다.")
        return

    client = get_s3_client(settings.data_s3_public)
    uploaded, failed = 0, 0

    for filename, file_date in _iter_rotated_log_files(settings.log_dir):
        local_path = os.path.join(settings.log_dir, filename)
        s3_key = f"{settings.log_s3_prefix}/{file_date}/{filename}"

        print(f"[upload_logs] 업로드 중: {local_path} -> s3://{settings.data_s3_bucket}/{s3_key}")
        if _upload_and_verify(local_path, settings.data_s3_bucket, s3_key, client):
            os.remove(local_path)
            print(f"[upload_logs] 업로드+검증 완료, 로컬 삭제: {local_path}")
            uploaded += 1
        else:
            failed += 1

    print(f"[upload_logs] 완료: 업로드 {uploaded}건, 실패(유지) {failed}건")


if __name__ == "__main__":
    main()
