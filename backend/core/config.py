from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    APP_HOST: str
    APP_PORT: int

    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PASSWORD: SecretStr
    MYSQL_DB: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: SecretStr

    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str
    JWT_EXPIRE_MINUTES: int

    RATE_LIMIT_PER_MINUTE: int
    WS_HEARTBEAT_TIMEOUT_SECONDS: int
    CORS_ALLOW_ORIGINS: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def mysql_password(self) -> str:
        return self.MYSQL_PASSWORD.get_secret_value()

    @property
    def redis_password(self) -> str:
        return self.REDIS_PASSWORD.get_secret_value()

    @property
    def jwt_secret_key(self) -> str:
        return self.JWT_SECRET_KEY.get_secret_value()

    @property
    def cors_allow_origins(self) -> list[str]:
        return [x.strip() for x in self.CORS_ALLOW_ORIGINS.split(",") if x.strip()]

settings = Settings()