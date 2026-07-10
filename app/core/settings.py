from pydantic_settings import BaseSettings
from pydantic import Field
from datetime import timedelta


class Settings(BaseSettings):
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_host: str = Field("localhost", alias="DB_HOST")
    db_port: int = Field(3306, alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")

    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_seconds: int = Field(900, alias="ACCESS_TOKEN_EXPIRE")
    refresh_token_expire_seconds: int = Field(604800, alias="REFRESH_TOKEN_EXPIRE")

    # Email (SMTP)
    smtp_host: str = Field("smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_user: str = Field("", alias="SMTP_USER")
    smtp_password: str = Field("", alias="SMTP_PASSWORD")
    smtp_from: str = Field("", alias="SMTP_FROM")
    email_code_expire_seconds: int = Field(300, alias="EMAIL_CODE_EXPIRE")

    # AI Server
    ai_server_url: str = Field("http://localhost:8090", alias="AI_SERVER_URL")

    # 맞춤형 정책 추천 카드 (임시 파일, 추후 policy 테이블 컬럼 + 추출 파이프라인으로 대체 예정)
    policy_cards_path: str = Field("./policy_cards.json", alias="POLICY_CARDS_PATH")

    # Google OAuth
    google_client_id: str = Field("", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field("http://localhost:8082/auth/google/callback", alias="GOOGLE_REDIRECT_URI")

    # Kakao OAuth
    kakao_client_id: str = Field("", alias="KAKAO_CLIENT_ID")
    kakao_client_secret: str = Field("", alias="KAKAO_CLIENT_SECRET")
    kakao_redirect_uri: str = Field("http://localhost:8082/auth/kakao/callback", alias="KAKAO_REDIRECT_URI")

    # Naver OAuth
    naver_client_id: str = Field("", alias="NAVER_CLIENT_ID")
    naver_client_secret: str = Field("", alias="NAVER_CLIENT_SECRET")
    naver_redirect_uri: str = Field("http://localhost:8082/auth/naver/callback", alias="NAVER_REDIRECT_URI")

    # AI 분석 마이크로서비스 (bene_ai) — ECS 태스크 정의에 이미 등록된 이름과 통일
    ai_service_url: str = Field("http://localhost:8090", alias="AI_SERVER_URL")

    frontend_url: str = Field("http://localhost:5173", alias="FRONTEND_URL")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
        populate_by_name = True

    @property
    def _base(self) -> str:
        return f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def db_url(self) -> str:
        return f"mysql+aiomysql://{self._base}"

    @property
    def sync_db_url(self) -> str:
        return f"mysql+pymysql://{self._base}"

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(seconds=self.access_token_expire_seconds)

    @property
    def refresh_token_expire(self) -> timedelta:
        return timedelta(seconds=self.refresh_token_expire_seconds)


settings = Settings()