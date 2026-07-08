import httpx
from fastapi import HTTPException, status
from app.core.settings import settings

class AiClient:

    @staticmethod
    async def recommend(user_profile: dict) -> dict:
        return await AiClient._post("/recommendations/", {"user_profile": user_profile})

    @staticmethod
    async def recommend_chat(user_profile: dict, chat: str) -> list[dict]:
        return await AiClient._post("/recommendations/chat", {"user_profile": user_profile, "chat": chat})

    @staticmethod
    async def resolve_scenario(
        region_choice: str, region_text: str | None, employment_choice: str, employment_other: str | None
    ) -> dict:
        """bene_ai의 구조화 질문(Q1 지역이동/Q2 취업 변화) diff 계산 호출. DB/Watson 미사용."""
        return await AiClient._post(
            "/recommendations/resolve-scenario",
            {
                "region_choice": region_choice,
                "region_text": region_text,
                "employment_choice": employment_choice,
                "employment_other": employment_other,
            },
        )

    @staticmethod
    async def _post(path: str, payload: dict):
        try:
            async with httpx.AsyncClient(base_url=settings.ai_server_url, timeout=30) as client:
                response = await client.post(path, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 서버 추천 요청에 실패했습니다.")
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI 서버에 연결할 수 없습니다.")
        
    # 코드분석 필요
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
