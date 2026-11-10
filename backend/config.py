
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables before initializing settings
load_dotenv()


class Settings(BaseSettings):

    # Application settings
    app_name: str = "AI HireMind"
    app_env: str = "development"
    debug: bool = False

    # Local MySQL settings
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "ai_hiremind"
    db_user: str = "hiremind_user"
    db_password: str = ""

    # Database provider
    database_provider: str = "mysql"

    # TiDB Cloud settings
    tidb_host: str | None = None
    tidb_port: int = 4000
    tidb_db_name: str = "ai_hiremind"
    tidb_user: str | None = None
    tidb_password: str | None = None
    ca_path: str | None = None

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
