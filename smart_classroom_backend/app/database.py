from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Определяем путь к базе данных в корне проекта
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'smart_classroom.db'}"

# Создаём движок SQLAlchemy
# check_same_thread=False необходим для SQLite в FastAPI (многопоточность)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Фабрика сессий - создаёт новые сессии БД при каждом запросе
# autocommit=False и autoflush=False для ручного управления транзакциями
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех ORM моделей
Base = declarative_base()


def get_db():
    """
    Dependency injection функция для FastAPI.
    Создаёт новую сессию БД для каждого запроса и гарантирует её закрытие.
    Используется в эндпоинтах через Depends(get_db).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
