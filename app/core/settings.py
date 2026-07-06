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