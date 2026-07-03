from app.services.image_analyze.detection import DetectionService
from app.services.image_analyze.ocr import OcrService
from app.services.image_analyze.search import SearchService
from app.services.image_analyze.llm import LlmService

TARGET_REGION_CLASSES = ("title", "text_area")


class ImageAnalyzeService:

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
              "matches": [
                {
                  "policy_id": int, "plcyNo": str, "plcyNm": str, "score": float,
                  "plcyExplnCn": str,
                  "sprtTrgtMinAge": int | None, "sprtTrgtMaxAge": int | None,
                  "plcySprtCn": str, "aplyYmd": str,
                  "plcyAplyMthdCn": str, "sbmsnDcmntCn": str,
                  "aplyUrlAddr": str,
                }, ...
              ],
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
                {
                    "policy_id": m["policy_id"],
                    "plcyNo": m["plcyNo"],
                    "plcyNm": m["plcyNm"],
                    "score": m["score"],
                    "plcyExplnCn": m["policy_raw"].get("plcyExplnCn") or "",
                    "sprtTrgtMinAge": m["policy_raw"].get("sprtTrgtMinAge"),
                    "sprtTrgtMaxAge": m["policy_raw"].get("sprtTrgtMaxAge"),
                    "plcySprtCn": m["policy_raw"].get("plcySprtCn") or "",
                    "aplyYmd": m["policy_raw"].get("aplyYmd") or m["policy_raw"].get("bizPrdEtcCn") or "",
                    "plcyAplyMthdCn": m["policy_raw"].get("plcyAplyMthdCn") or "",
                    "sbmsnDcmntCn": m["policy_raw"].get("sbmsnDcmntCn") or "",
                    "aplyUrlAddr": m["policy_raw"].get("aplyUrlAddr") or "",
                }
                for m in matches
            ],
            "summary_text": summary_text,
            "message": None,
        }