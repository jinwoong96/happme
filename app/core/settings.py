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

    crop_padding: float = Field(0.05, alias="CROP_PADDING")

    # 정책 검색 (Sentence-BERT)
    policy_json_path: str = Field(..., alias="POLICY_JSON_PATH")
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

    # 정책 일정 추출 (rule-engine + LLM)
    schedule_model_id: str = Field("mistralai/mistral-small-3-1-24b-instruct-2503", alias="SCHEDULE_MODEL_ID")

    # 서비스
    temp_upload_dir: str = Field("./tmp_uploads", alias="TEMP_UPLOAD_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
        populate_by_name = True


settings = Settings()
os.makedirs(settings.temp_upload_dir, exist_ok=True)