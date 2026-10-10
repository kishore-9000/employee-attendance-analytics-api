"""
app/core/config.py
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "attendance_db"

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Logging
    log_level: str = "INFO"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"


settings = Settings()
