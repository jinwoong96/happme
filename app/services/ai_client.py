"""
bene_ai(이미지 분석 마이크로서비스) 호출 전용 얇은 클라이언트.
OcrResultService 등 여러 서비스에서 재사용할 수 있게 분리해뒀습니다.
"""
import httpx
from fastapi import HTTPException, status

from app.core.settings import settings


class AiClient:

    @staticmethod
    async def analyze_image(image_bytes: bytes, filename: str, content_type: str) -> dict:
        """
        bene_ai의 POST /image-analyze/ 호출.
        Returns: {extracted_text, detected_objects, matches:[{policy_id, plcyNo, plcyNm, score}], summary_text, message}
        """
        url = f"{settings.ai_service_url}/image-analyze/"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": (filename, image_bytes, content_type or "image/jpeg")}
                resp = await client.post(url, files=files)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI 분석 서비스 호출에 실패했습니다: {e}",
            )