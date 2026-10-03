import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Определяем путь к локальной SQLite-базе
BASE_DIR = Path(__file__).resolve().parent.parent

# На Render будет использоваться DATABASE_URL из Environment.
# Локально, если переменной нет, останется SQLite.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'smart_classroom.db'}"
)

# Render иногда может предоставить postgres://
# SQLAlchemy использует postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# Настройки движка
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс для ORM-моделей
Base = declarative_base()


def get_db():
    """
    Создаёт отдельную сессию БД для каждого запроса
    и гарантирует её закрытие.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
