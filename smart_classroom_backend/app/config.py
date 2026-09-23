from pathlib import Path
from typing import Optional
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


# Определяем базовую директорию проекта для корректной работы с путями
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """
    Конфигурация приложения с валидацией через Pydantic.
    Все настройки могут быть переопределены через переменные окружения.
    """
    
    # Security - настройки для JWT токенов
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database - строка подключения к БД
    database_url: str = f"sqlite:///{BASE_DIR}/smart_classroom.db"
    
    # CORS - разрешённые origins для cross-origin запросов
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Rate limiting - максимальное количество запросов в минуту
    max_requests_per_minute: int = 100
    
    # Logging - уровень логирования
    log_level: str = "INFO"
    
    # Pydantic конфигурация для загрузки из .env файла
    model_config = {
        "env_file": BASE_DIR / ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Глобальный экземпляр настроек для использования во всём приложении
settings = Settings()

