import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # 공고물 위치 탐지기 (banner/poster/card_news) — Faster R-CNN
    notice_detector_weights: str = Field("", alias="NOTICE_DETECTOR_WEIGHTS")
    notice_detector_conf: float = Field(0.9, alias="NOTICE_DETECTOR_CONF")
    notice_detector_num_classes: int = Field(5, alias="NOTICE_DETECTOR_NUM_CLASSES")
    notice_detector_coco_ann: str = Field("", alias="NOTICE_DETECTOR_COCO_ANN")

    # 텍스트 영역 탐지기 (title/text_area) — YOLOv11n
    text_region_detector_weights: str = Field("", alias="TEXT_REGION_DETECTOR_WEIGHTS")
    text_region_detector_conf: float = Field(0.5, alias="TEXT_REGION_DETECTOR_CONF")

    # 모델 가중치 S3 자동 다운로드 (git에는 올리지 않고, 서버 시작 시 없으면 내려받음)
    # MODEL_S3_BUCKET이 비어있으면 다운로드를 건너뛰고 로컬 파일을 그대로 사용합니다.
    model_s3_bucket: str = Field("", alias="MODEL_S3_BUCKET")
    model_s3_public: bool = Field(False, alias="MODEL_S3_PUBLIC")
    notice_detector_s3_key: str = Field("", alias="NOTICE_DETECTOR_S3_KEY")
    text_region_detector_s3_key: str = Field("", alias="TEXT_REGION_DETECTOR_S3_KEY")

    crop_padding: float = Field(0.05, alias="CROP_PADDING")

    # 업로드/추론 안전장치
    max_upload_size_mb: int = Field(10, alias="MAX_UPLOAD_SIZE_MB")
    max_image_pixels: int = Field(20_000_000, alias="MAX_IMAGE_PIXELS")  # 약 20MP

    # 사전 계산된 임베딩/정책 원본 파일 S3 자동 다운로드 (git에는 올리지 않고, 서버 시작 시
    # 없으면 내려받음). DATA_S3_BUCKET이 비어있으면 다운로드를 건너뛰고 로컬 파일을 그대로
    # 사용합니다. policy_embedding_cache/policy_summary_embed_cache는 원본(DB/JSON)이 더
    # 최신이라 로컬에서 재계산되면, 그 결과를 다시 S3에 업로드해 다음 배포부터 최신 캐시를
    # 받아가도록 합니다. 나머지(유사도 검색용 정적 임베딩 등)는 앱 안에 재계산 로직이 없는
    # 정적 자산이라 다운로드만 합니다.
    # (정책 원본 JSON은 서버 런타임에서는 PolicyLoaderService가 DB를 직접 조회하므로 쓰이지
    # 않지만, run_create_policy_cards.py 등 오프라인 배치 스크립트가 입력으로 사용하므로
    # policy_list.json도 여기서 함께 내려받습니다.)
    data_s3_bucket: str = Field("", alias="DATA_S3_BUCKET")
    data_s3_public: bool = Field(False, alias="DATA_S3_PUBLIC")
    policy_list_path: str = Field("./data/policy_list.json", alias="POLICY_LIST_PATH")
    policy_list_s3_key: str = Field("", alias="POLICY_LIST_S3_KEY")
    zipcd_mapping_s3_key: str = Field("", alias="ZIPCD_MAPPING_S3_KEY")
    similarity_docs_s3_key: str = Field("", alias="SIMILARITY_DOCS_S3_KEY")
    similarity_embeddings_s3_key: str = Field("", alias="SIMILARITY_EMBEDDINGS_S3_KEY")
    policy_embedding_cache_s3_key: str = Field("", alias="POLICY_EMBEDDING_CACHE_S3_KEY")
    policy_summary_embed_cache_s3_key: str = Field("", alias="POLICY_SUMMARY_EMBED_CACHE_S3_KEY")

    # 정책 검색 (Sentence-BERT)
    # 정책 데이터는 bene_backend와 동일한 RDS MySQL(policy 테이블)에서 읽어옵니다.
    db_host: str = Field(..., alias="DB_HOST")
    db_port: int = Field(3306, alias="DB_PORT")
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_name: str = Field(..., alias="DB_NAME")

    embedding_model_name: str = Field("jhgan/ko-sroberta-multitask", alias="EMBEDDING_MODEL_NAME")
    policy_embedding_cache: str = Field("./policy_embeddings.npy", alias="POLICY_EMBEDDING_CACHE")
    top_k: int = Field(3, alias="TOP_K")

    # 맞춤형 정책 추천 (rule engine)
    zipcd_mapping_path: str = Field("./data/zipcd_mapping.csv", alias="ZIPCD_MAPPING_PATH")

    # 채팅 기반 정책 유사도 검색
    similarity_model_name: str = Field("BAAI/bge-m3", alias="SIMILARITY_MODEL_NAME")
    similarity_embeddings_path: str = Field(
        "./data/embeddings/search_docs_full_text_embeddings.npy", alias="SIMILARITY_EMBEDDINGS_PATH"
    )
    similarity_docs_path: str = Field("./data/policy_search_docs.json", alias="SIMILARITY_DOCS_PATH")

    # OCR
    ocr_lang: str = Field("korean", alias="OCR_LANG")
    ocr_device: str = Field("cpu", alias="OCR_DEVICE")
    ocr_min_score: float = Field(0.5, alias="OCR_MIN_SCORE")
    # 공고문 이미지 판별용 최소 추출 텍스트 길이 (이보다 짧으면 "텍스트 추출 실패"로 처리)
    ocr_min_text_length: int = Field(5, alias="OCR_MIN_TEXT_LENGTH")

    # 정책 매칭 최소 유사도 (이보다 낮으면 "일치하는 정책 없음"으로 처리 -> 공고문이 아닌 사진 필터링)
    match_min_score: float = Field(0.4, alias="MATCH_MIN_SCORE")

    # watsonx.ai
    watsonx_url: str = Field("https://us-south.ml.cloud.ibm.com", alias="WATSONX_URL")
    watsonx_api_key: str = Field("", alias="WATSONX_API_KEY")
    watsonx_project_id: str = Field("", alias="WATSONX_PROJECT_ID")
    watsonx_model_id: str = Field("mistralai/mistral-small-3-1-24b-instruct-2503", alias="WATSONX_MODEL_ID")
    enable_llm_summary: bool = Field(True, alias="ENABLE_LLM_SUMMARY")

    # 정책 일정 추출 (rule-engine + LLM)
    schedule_model_id: str = Field("mistralai/mistral-small-3-1-24b-instruct-2503", alias="SCHEDULE_MODEL_ID")

    # 서비스
    temp_upload_dir: str = Field("./tmp_uploads", alias="TEMP_UPLOAD_DIR")

    # 청년정책 PDF/텍스트/URL 요약 (policy_summary). 정책 원본은 PdfSummaryService가
    # SearchService/PolicyLoaderService처럼 DB를 직접 조회하므로 별도 JSON 경로가 없다.
    policy_summary_embed_model: str = Field("intfloat/multilingual-e5-large", alias="POLICY_SUMMARY_EMBED_MODEL")
    policy_summary_embed_cache: str = Field("./policy_summary_embeddings_cache.npz", alias="POLICY_SUMMARY_EMBED_CACHE")
    policy_summary_llm_model_id: str = Field("mistralai/mistral-small-3-1-24b-instruct-2503", alias="POLICY_SUMMARY_LLM_MODEL_ID")

    # 모니터링
    app_env: str = Field("development", alias="APP_ENV")
    sentry_dsn: str = Field("", alias="SENTRY_DSN")
    sentry_environment: str = Field("", alias="SENTRY_ENVIRONMENT")
    slack_webhook_url: str = Field("", alias="SLACK_WEBHOOK_URL")
    log_dir: str = Field("./logs", alias="LOG_DIR")
    # 날짜별로 로테이션된 로그(ai.log.YYYY-MM-DD, steps.jsonl.YYYY-MM-DD)를 업로드할 위치.
    # 버킷은 모델/데이터와 같은 DATA_S3_BUCKET을 재사용하고, prefix만 분리한다.
    log_s3_prefix: str = Field("ai-storage/logs", alias="LOG_S3_PREFIX")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
        populate_by_name = True


settings = Settings()
os.makedirs(settings.temp_upload_dir, exist_ok=True)