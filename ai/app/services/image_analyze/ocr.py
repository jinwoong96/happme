import os
import re
import uuid

import numpy as np
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
            device=settings.ocr_device,
            # CPU 추론 시 PaddleOCR가 oneDNN(mkldnn)을 자동으로 켜는데,
            # 현재 paddlepaddle-gpu==3.3.0의 PIR 실행기 + oneDNN 조합에서
            # 일부 연산자(double 배열 속성)가 미구현이라 NotImplementedError가 남.
            # 해결될 때까지 명시적으로 비활성화.
            enable_mkldnn=False,
        )
        # numpy 배열을 직접 predict()에 넣을 수 있는지 최초 1회만 확인해서 캐싱
        # (지원 안 되면 매 요청마다 임시파일 방식으로 폴백)
        self._supports_ndarray_input = True
        print("[OcrService] 준비 완료")

    @staticmethod
    def _clean_text(text: str) -> str:
        """OCR로 읽은 텍스트에서 특수문자를 지우고 공백을 정리한다."""
        text = re.sub(r"[^\w\s가-힣]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _run_ocr(self, img) -> list:
        """
        가능하면 numpy 배열로 바로 predict() 호출(디스크 왕복 없음).
        실패하면(버전 차이 등) 임시파일 방식으로 폴백.
        """
        rgb_img = img.convert("RGB")

        if self._supports_ndarray_input:
            try:
                return self.ocr_engine.predict(np.array(rgb_img))
            except Exception as e:
                print(f"[OcrService] numpy 입력 실패, 파일 방식으로 폴백: {e}")
                self._supports_ndarray_input = False

        tmp_path = os.path.join(settings.temp_upload_dir, f"{uuid.uuid4().hex}.jpg")
        rgb_img.save(tmp_path, quality=95)
        try:
            return self.ocr_engine.predict(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def extract_svc(self, crop_images: list, min_score: float = None) -> list[dict]:
        """
        crop_images: PIL.Image 리스트 (title/text_area crop)
        Returns: [{"raw_text": str, "cleaned_text": str, "score": float}, ...]
        """
        min_score = settings.ocr_min_score if min_score is None else min_score
        results = []

        for img in crop_images:
            ocr_out = self._run_ocr(img)
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

        return results

    def extract_combined_text_svc(self, crop_images: list, min_score: float = None) -> str:
        """모든 crop에서 뽑은 텍스트를 하나의 문자열로 합쳐서 반환 (검색 쿼리 / DB 저장용)"""
        results = self.extract_svc(crop_images, min_score=min_score)
        return " ".join(r["cleaned_text"] for r in results)