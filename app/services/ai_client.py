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
