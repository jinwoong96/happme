import time
from concurrent.futures import ThreadPoolExecutor

from app.services.image_analyze.detection import DetectionService
from app.services.image_analyze.ocr import OcrService
from app.services.image_analyze.search import SearchService
from app.services.image_analyze.llm import LlmService
from app.core.settings import settings

TARGET_REGION_CLASSES = ("title", "text_area")

# 정책 공고문에는 거의 항상 등장하는 행정 용어.
# 의미 유사도(임베딩)만으로는 무관한 텍스트도 우연히 일정 점수를 넘길 수 있어서(모델의
# anisotropy로 인한 유사도 하한선 문제), 이 키워드가 하나도 없으면 매칭을 무효화하는
# 2차 게이트로 사용한다.
POLICY_KEYWORDS = (
    "청년", "지원", "신청", "모집", "사업", "정책", "대상자", "대상",
    "지원금", "선발", "접수", "공고", "안내문", "혜택", "바우처", "장려금",
    "지원사업", "신청기간", "신청방법", "지원대상", "모집공고",
)


def _has_policy_keyword(text: str) -> bool:
    return any(keyword in text for keyword in POLICY_KEYWORDS)


MSG_NO_NOTICE_DETECTED = (
    "공고문(배너·포스터·카드뉴스) 형태의 이미지가 아닌 것 같아요. "
    "청년정책 공고 이미지를 업로드해주세요."
)
MSG_NO_TEXT_REGION = (
    "이미지에서 제목이나 본문 텍스트 영역을 찾지 못했어요. "
    "글자가 잘 보이는 사진으로 다시 시도해주세요."
)
MSG_OCR_TOO_SHORT = (
    "이미지에서 텍스트를 충분히 읽어내지 못했어요. "
    "더 선명하고 글자가 잘 보이는 사진으로 다시 시도해주세요."
)
MSG_NO_MATCH = (
    "업로드하신 이미지와 일치하는 청년정책을 찾지 못했어요. "
    "정책 공고문 이미지가 맞는지 확인해주세요."
)


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

    @staticmethod
    def _empty_result(detected_objects: int, message: str, extracted_text: str = "") -> dict:
        return {
            "extracted_text": extracted_text,
            "detected_objects": detected_objects,
            "matches": [],
            "summary_text": None,
            "message": message,
        }

    def analyze_svc(self, image_path: str) -> dict:
        """
        이미지 경로 하나를 받아 전체 파이프라인을 실행하고 결과를 반환합니다.

        정책 공고문이 아닌 이미지(무관한 사진 등)를 단계별로 걸러내기 위해
        아래 순서로 검사하며, 어느 단계에서든 실패하면 그 단계에 맞는
        message와 함께 빈 결과를 반환합니다.
          1) 공고물(배너/포스터/카드뉴스) 탐지 실패
          2) title/text_area 텍스트 영역 탐지 실패
          3) OCR 추출 텍스트가 너무 짧음
          4) 정책 매칭 유사도가 임계값 미만 (모든 후보 탈락)

        Returns:
            {
              "extracted_text": str,
              "detected_objects": int,
              "matches": [
                {
                  "policy_id": int, "plcyNo": str, "plcyNm": str, "score": float,
                  "plcyExplnCn": str, "plcyExplnSummary": str,
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
        t0 = time.perf_counter()
        detection_result = self.detection_service.detect_svc(image_path)
        t1 = time.perf_counter()
        objects = detection_result["objects"]

        # 1) 공고물류 자체를 하나도 못 찾음 -> 공고문 이미지가 아닐 가능성이 높음
        if not objects:
            print(f"[timing] detection={t1 - t0:.2f}s (공고물 없음, 종료)")
            return self._empty_result(0, MSG_NO_NOTICE_DETECTED)

        crop_images = [
            region["crop_image"]
            for obj in objects
            for region in obj["regions"]
            if region["class"] in TARGET_REGION_CLASSES
        ]

        # 2) 공고물은 찾았지만 제목/본문 텍스트 영역이 없음
        if not crop_images:
            print(f"[timing] detection={t1 - t0:.2f}s (텍스트 영역 없음, 종료)")
            return self._empty_result(len(objects), MSG_NO_TEXT_REGION)

        t2 = time.perf_counter()
        extracted_text = self.ocr_service.extract_combined_text_svc(crop_images)
        t3 = time.perf_counter()

        # 3) 텍스트 영역은 있었지만 OCR로 의미 있는 글자를 거의 읽어내지 못함
        if len(extracted_text.strip()) < settings.ocr_min_text_length:
            print(f"[timing] detection={t1 - t0:.2f}s ocr={t3 - t2:.2f}s (텍스트 부족, 종료)")
            return self._empty_result(len(objects), MSG_OCR_TOO_SHORT, extracted_text)

        t4 = time.perf_counter()
        matches = self.search_service.search_policy_svc(extracted_text)
        t5 = time.perf_counter()

        # 4) 정책 후보는 나왔지만 (a) 유사도가 임계값 미만이거나
        #    (b) 정책 공고문에 흔한 키워드가 텍스트에 전혀 없으면 -> 무관한 이미지로 판단
        matches = [m for m in matches if m["score"] >= settings.match_min_score]
        if matches and not _has_policy_keyword(extracted_text):
            matches = []
        if not matches:
            print(
                f"[timing] detection={t1 - t0:.2f}s ocr={t3 - t2:.2f}s "
                f"search={t5 - t4:.2f}s (매칭 없음, 종료)"
            )
            return self._empty_result(len(objects), MSG_NO_MATCH, extracted_text)

        t6 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2) as executor:
            summary_future = executor.submit(self.llm_service.summarize_svc, extracted_text, matches)
            one_liner_future = executor.submit(self.llm_service.summarize_one_liners_svc, matches)
            summary_text = summary_future.result()
            one_liners = one_liner_future.result()
        t7 = time.perf_counter()

        print(
            f"[timing] detection={t1 - t0:.2f}s ocr={t3 - t2:.2f}s "
            f"search={t5 - t4:.2f}s llm={t7 - t6:.2f}s total={t7 - t0:.2f}s"
        )

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
                    "plcyExplnSummary": one_liners.get(m["policy_id"]) or "",
                    "sprtTrgtMinAge": m["policy_raw"].get("sprtTrgtMinAge"),
                    "sprtTrgtMaxAge": m["policy_raw"].get("sprtTrgtMaxAge"),
                    "plcySprtCn": m["policy_raw"].get("plcySprtCn") or "",
                    "aplyYmd": m["policy_raw"].get("aplyYmd") or m["policy_raw"].get("bizPrdEtcCn") or "",
                    "plcyAplyMthdCn": m["policy_raw"].get("plcyAplyMthdCn") or "",
                    "sbmsnDcmntCn": m["policy_raw"].get("sbmsnDcmntCn") or "",
                    "aplyUrlAddr": m["policy_raw"].get("aplyUrlAddr") or "",
                    "refUrlAddr1": m["policy_raw"].get("refUrlAddr1") or "",
                    "refUrlAddr2": m["policy_raw"].get("refUrlAddr2") or "",
                }
                for m in matches
            ],
            "summary_text": summary_text,
            "message": None,
        }