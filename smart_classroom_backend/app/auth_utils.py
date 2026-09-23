import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

from . import config  # noqa: F401

# Секретный ключ для JWT подписи - должен быть сложным и уникальным
SECRET_KEY = os.getenv("SMART_CLASSROOM_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SMART_CLASSROOM_SECRET_KEY environment variable is required")

# JWT настройки
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Контекст для хеширования паролей с использованием pbkdf2_sha256
# deprecated="auto" означает автоматический выбор лучших алгоритмов
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str):
    """
    Хеширует пароль с использованием pbkdf2_sha256.
    Хеширование необратимо - пароль нельзя восстановить из хеша.
    """
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    """
    Проверяет соответствие plain текста пароля его хешу.
    Возвращает True если пароли совпадают, иначе False.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(*, user_id: int, email: str, role: str):
    """
    Создаёт JWT access токен для аутентификации пользователя.
    
    Параметры:
        user_id: ID пользователя в БД
        email: email пользователя (используется как subject в JWT)
        role: роль пользователя (student/teacher/admin)
    
    Возвращает:
        Закодированный JWT токен string
    
    Токен содержит:
        sub: email пользователя (subject)
        user_id: ID пользователя
        role: роль для авторизации
        type: "access" для differentiation от refresh токенов
        iat: время создания (issued at)
        exp: время истечения (expiration)
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "user_id": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
