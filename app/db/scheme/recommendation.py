from pydantic import BaseModel


class ChatRecommendationRequest(BaseModel):
    chat: str
