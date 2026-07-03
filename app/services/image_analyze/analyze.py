from app.services.image_analyze.detection import DetectionService
from app.services.image_analyze.ocr import OcrService
from app.services.image_analyze.search import SearchService
from app.services.image_analyze.llm import LlmService

TARGET_REGION_CLASSES = ("title", "text_area")


class ImageAnalyzeService:
    """
    탐지 -> OCR -> 정책 검색 -> LLM 요약을 순서대로 실행하는 오케스트레이션 서비스.
    각 하위 서비스(DetectionService/OcrService/SearchService/LlmService)는
    무거운 모델을 들고 있으므로, 앱 시작 시(lifespan) 한 번만 생성해서 주입받아 재사용하세요.
    """

    def __init__(
        self,
        detection_service: DetectionService,
        ocr_service: OcrService,
        search_service: SearchService,
        llm_service: LlmService,
    ):
        self.detection_service = detection_service
        self.ocr_service = ocr_service
        self.search_service = search_service
        self.llm_service = llm_service

    def analyze_svc(self, image_path: str) -> dict:
        """
        이미지 경로 하나를 받아 전체 파이프라인을 실행하고 결과를 반환합니다.

        Returns:
            {
              "extracted_text": str,
              "detected_objects": int,
              "matches": [{"plcyNo": str, "plcyNm": str, "score": float}, ...],
              "summary_text": str | None,
              "message": str | None,
            }
        """
        detection_result = self.detection_service.detect_svc(image_path)
        objects = detection_result["objects"]

        crop_images = [
            region["crop_image"]
            for obj in objects
            for region in obj["regions"]
            if region["class"] in TARGET_REGION_CLASSES
        ]

        if not crop_images:
            return {
                "extracted_text": "",
                "detected_objects": len(objects),
                "matches": [],
                "summary_text": None,
                "message": "이미지에서 title/text_area 영역을 찾지 못했습니다.",
            }

        extracted_text = self.ocr_service.extract_combined_text_svc(crop_images)
        matches = self.search_service.search_policy_svc(extracted_text)
        summary_text = self.llm_service.summarize_svc(extracted_text, matches)

        return {
            "extracted_text": extracted_text,
            "detected_objects": len(objects),
            "matches": [
                {"plcyNo": m["plcyNo"], "plcyNm": m["plcyNm"], "score": m["score"]}
                for m in matches
            ],
            "summary_text": summary_text,
            "message": None,
        }