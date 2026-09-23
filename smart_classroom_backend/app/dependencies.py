from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import models
from .auth_utils import ALGORITHM, SECRET_KEY
from .database import get_db

# OAuth2 схема для извлечения Bearer токена из Authorization header
# tokenUrl указывает на endpoint для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Dependency для аутентификации пользователя через JWT токен.
    
    Процесс:
    1. Извлекает Bearer токен из Authorization header
    2. Декодирует и валидирует JWT токен
    3. Проверяет наличие обязательных полей (sub, user_id, role, type)
    4. Ищет пользователя в БД по user_id
    5. Проверяет совпадение email и role с токеном
    
    Возвращает:
        models.User объект если аутентификация успешна
    
    Выбрасывает:
        HTTPException 401 если токен невалиден или пользователь не найден
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role")
        token_type = payload.get("type")
        
        # Проверка обязательных полей и типа токена
        if email is None or user_id is None or role is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    # Поиск пользователя в БД
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Дополнительная проверка - данные пользователя не должны измениться
    if user.email != email or user.role.lower() != str(role).lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return user


def require_role(*roles: str):
    """
    Factory функция для создания dependency для проверки ролей.
    
    Использование:
        @router.get("/admin-only")
        def admin_endpoint(user=Depends(require_role("admin"))):
            return {"message": "Admin access"}
    
    Параметры:
        *roles: список разрешённых ролей
    
    Возвращает:
        Dependency функцию которая проверяет роль пользователя
    """
    normalized_roles = {role.lower() for role in roles}

    def checker(user=Depends(get_current_user)):
        if normalized_roles and user.role.lower() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return user

    return checker
