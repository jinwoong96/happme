import os
import re
import uuid

from paddleocr import PaddleOCR

from app.core.settings import settings


class OcrService:
    """
    PaddleOCR 기반 텍스트 추출 서비스.
    무거운 모델을 들고 있으므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        print("[OcrService] PaddleOCR 로드 중...")
        self.ocr_engine = PaddleOCR(
            lang=settings.ocr_lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        print("[OcrService] 준비 완료")

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"[^\w\s가-힣]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_svc(self, crop_images: list, min_score: float = None) -> list[dict]:
        """
        crop_images: PIL.Image 리스트 (title/text_area crop)
        Returns: [{"raw_text": str, "cleaned_text": str, "score": float}, ...]
        """
        min_score = settings.ocr_min_score if min_score is None else min_score
        results = []

        for img in crop_images:
            tmp_path = os.path.join(settings.temp_upload_dir, f"{uuid.uuid4().hex}.jpg")
            img.convert("RGB").save(tmp_path, quality=95)
            try:
                ocr_out = self.ocr_engine.predict(tmp_path)
                for line in ocr_out:
                    texts = line.get("rec_texts", [])
                    scores = line.get("rec_scores", [])
                    for t, s in zip(texts, scores):
                        if s < min_score:
                            continue
                        cleaned = self._clean_text(t)
                        if not cleaned:
                            continue
                        results.append({"raw_text": t, "cleaned_text": cleaned, "score": float(s)})
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        return results

    def extract_combined_text_svc(self, crop_images: list, min_score: float = None) -> str:
        """모든 crop에서 뽑은 텍스트를 하나의 문자열로 합쳐서 반환 (검색 쿼리 / DB 저장용)"""
        results = self.extract_svc(crop_images, min_score=min_score)
        return " ".join(r["cleaned_text"] for r in results)