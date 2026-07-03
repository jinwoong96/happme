import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # 공고물 위치 탐지기 (banner/poster/card_news) — Faster R-CNN
    notice_detector_weights: str = Field(..., alias="NOTICE_DETECTOR_WEIGHTS")
    notice_detector_conf: float = Field(0.9, alias="NOTICE_DETECTOR_CONF")
    notice_detector_num_classes: int = Field(5, alias="NOTICE_DETECTOR_NUM_CLASSES")
    notice_detector_coco_ann: str = Field("", alias="NOTICE_DETECTOR_COCO_ANN")

    # 텍스트 영역 탐지기 (title/text_area) — YOLOv11n
    text_region_detector_weights: str = Field(..., alias="TEXT_REGION_DETECTOR_WEIGHTS")
    text_region_detector_conf: float = Field(0.5, alias="TEXT_REGION_DETECTOR_CONF")

    # 모델 가중치 S3 자동 다운로드 (git에는 올리지 않고, 서버 시작 시 없으면 내려받음)
    # MODEL_S3_BUCKET이 비어있으면 다운로드를 건너뛰고 로컬 파일을 그대로 사용합니다.
    model_s3_bucket: str = Field("", alias="MODEL_S3_BUCKET")
    model_s3_public: bool = Field(False, alias="MODEL_S3_PUBLIC")
    notice_detector_s3_key: str = Field("", alias="NOTICE_DETECTOR_S3_KEY")
    text_region_detector_s3_key: str = Field("", alias="TEXT_REGION_DETECTOR_S3_KEY")

    crop_padding: float = Field(0.05, alias="CROP_PADDING")

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

    # OCR
    ocr_lang: str = Field("korean", alias="OCR_LANG")
    ocr_min_score: float = Field(0.5, alias="OCR_MIN_SCORE")

    # watsonx.ai
    watsonx_url: str = Field("https://us-south.ml.cloud.ibm.com", alias="WATSONX_URL")
    watsonx_api_key: str = Field("", alias="WATSONX_API_KEY")
    watsonx_project_id: str = Field("", alias="WATSONX_PROJECT_ID")
    watsonx_model_id: str = Field("meta-llama/llama-3-3-70b-instruct", alias="WATSONX_MODEL_ID")
    enable_llm_summary: bool = Field(True, alias="ENABLE_LLM_SUMMARY")

    # 서비스
    temp_upload_dir: str = Field("./tmp_uploads", alias="TEMP_UPLOAD_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
        populate_by_name = True


settings = Settings()
os.makedirs(settings.temp_upload_dir, exist_ok=True)