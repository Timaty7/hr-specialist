"""
Жаңартылған конфигурация. 
Құдіретті жасаушының (Creator) идентификаторы қауіпсіз қосылды.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres_password@db:5432/smart_chef"
    REDIS_URL: str = "redis://redis:6379/0"
    GOOGLE_SHEET_ID: str = ""
    
    # Криатор идентификаторы (Мәжбүрлі түрде int форматына айналады)
    CREATOR_ID: int

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()