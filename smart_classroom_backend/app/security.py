"""
Security utilities for Smart Classroom Backend
"""

import re
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Пароль должен быть не менее 8 символов")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Пароль должен содержать хотя бы одну заглавную букву")
    
    if not re.search(r'[a-z]', password):
        errors.append("Пароль должен содержать хотя бы одну строчную букву")
    
    if not re.search(r'[0-9]', password):
        errors.append("Пароль должен содержать хотя бы одну цифру")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Пароль должен содержать хотя бы один специальный символ")
    
    return len(errors) == 0, errors


def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent XSS attacks"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r']
    sanitized = input_string
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def validate_student_data(data: dict) -> tuple[bool, list[str]]:
    """Validate student data"""
    errors = []
    
    if not data.get('full_name'):
        errors.append("ФИО обязательно")
    elif len(data['full_name']) < 3:
        errors.append("ФИО должно быть не менее 3 символов")
    
    if not data.get('email'):
        errors.append("Email обязателен")
    elif not validate_email(data['email']):
        errors.append("Некорректный формат email")
    
    if not data.get('group_name'):
        errors.append("Группа обязательна")
    
    return len(errors) == 0, errors


def validate_teacher_data(data: dict) -> tuple[bool, list[str]]:
    """Validate teacher data"""
    errors = []
    
    if not data.get('full_name'):
        errors.append("ФИО обязательно")
    elif len(data['full_name']) < 3:
        errors.append("ФИО должно быть не менее 3 символов")
    
    if not data.get('email'):
        errors.append("Email обязателен")
    elif not validate_email(data['email']):
        errors.append("Некорректный формат email")
    
    if not data.get('subject'):
        errors.append("Предмет обязателен")
    
    return len(errors) == 0, errors


def validate_course_data(data: dict) -> tuple[bool, list[str]]:
    """Validate course data"""
    errors = []
    
    if not data.get('name'):
        errors.append("Название курса обязательно")
    elif len(data['name']) < 3:
        errors.append("Название курса должно быть не менее 3 символов")
    
    if not data.get('teacher_id'):
        errors.append("ID преподавателя обязателен")
    
    return len(errors) == 0, errors


def rate_limit_check(identifier: str, max_requests: int = 100, window_minutes: int = 60) -> tuple[bool, int]:
    """
    Simple rate limiting check
    In production, use Redis or similar for distributed rate limiting
    Returns (is_allowed, remaining_requests)
    """
    # This is a placeholder - implement with Redis or similar in production
    # For now, always allow requests
    return True, max_requests
