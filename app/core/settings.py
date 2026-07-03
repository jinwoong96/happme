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

    ai_service_url: str = Field("http://localhost:8090", alias="AI_SERVICE_URL")

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
