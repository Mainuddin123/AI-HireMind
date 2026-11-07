
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Application settings
    app_name: str = "AI HireMind"
    app_env: str = "development"
    debug: bool = False

    # MySQL database settings
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "ai_hiremind"
    db_user: str = "hiremind_user"
    db_password: str

    # JWT authentication settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
