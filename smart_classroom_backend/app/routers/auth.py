from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..auth_utils import create_access_token, hash_password, verify_password
from ..database import get_db
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Auth"])


def _to_user_response(user):
    """
    Преобразует модель User в UserResponse схему.
    Включает ID связанного teacher или student профиля если есть.
    """
    return schemas.UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        teacher_id=user.teacher_profile.id if user.teacher_profile else None,
        student_id=user.student_profile.id if user.student_profile else None,
    )


def _to_user_admin_response(user):
    """
    Упрощённая версия UserResponse для админских операций.
    Не включает ID профилей для безопасности.
    """
    return schemas.UserAdminResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
    )


@router.get("/me", response_model=schemas.UserResponse)
def get_me(user=Depends(get_current_user)):
    """
    Возвращает информацию о текущем аутентифицированном пользователе.
    Требует валидный JWT токен в Authorization header.
    """
    return _to_user_response(user)


@router.post("/change-password", response_model=schemas.UserResponse)
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Изменяет пароль текущего пользователя.
    Требует подтверждения текущего пароля.
    """
    if not verify_password(payload.current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.password = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.put("/me", response_model=schemas.UserResponse)
def update_me(
    payload: schemas.UserUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Обновляет профиль текущего пользователя.
    Изменения зависят от роли (student/teacher).
    """
    updated_user = crud.update_user_account(db, user, payload)
    return _to_user_response(updated_user)


@router.post("/register", response_model=schemas.TokenResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Публичная регистрация новых пользователей.
    Доступна только для создания student аккаунтов.
    Преподаватели и админы создаются через register-staff.
    """
    if user.role.lower() != "student":
        raise HTTPException(
            status_code=403,
            detail="Public registration is available only for students",
        )
    if not user.group_name or not user.group_name.strip():
        raise HTTPException(status_code=400, detail="Group is required for student registration")

    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    created_user = crud.create_user(db, user)
    access_token = create_access_token(user_id=created_user.id, email=created_user.email, role=created_user.role)
    return schemas.TokenResponse(access_token=access_token)


@router.post(
    "/register-staff",
    response_model=schemas.UserResponse,
    dependencies=[Depends(require_role("admin"))],
)
def register_staff(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создание аккаунтов преподавателей и администраторов.
    Доступно только пользователям с ролью admin.
    """
    if user.role.lower() not in {"teacher", "admin", "student"}:
        raise HTTPException(
            status_code=400,
            detail="Account creation supports teacher, student, or admin roles",
        )
    if user.role.lower() == "teacher" and (not user.subject or not user.subject.strip()):
        raise HTTPException(status_code=400, detail="Subject is required for teacher accounts")
    if user.role.lower() == "student" and (not user.group_name or not user.group_name.strip()):
        raise HTTPException(status_code=400, detail="Group is required for student accounts")

    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    created_user = crud.create_user(db, user)
    return _to_user_response(created_user)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Аутентификация пользователя и выдача JWT токена.
    Поддерживает как JSON так и form-data формат.
    """
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        raw_payload = await request.json()
        email = raw_payload.get("email")
        raw_password = raw_payload.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        raw_password = form.get("password")

    if not email or not raw_password:
        raise HTTPException(status_code=422, detail="Email and password are required")

    try:
        login_payload = schemas.UserLogin(email=email, password=raw_password)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid login payload") from exc

    db_user = crud.get_user_by_email(db, str(login_payload.email))

    if db_user is None or not verify_password(login_payload.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        user_id=db_user.id,
        email=db_user.email,
        role=db_user.role,
    )

    return schemas.TokenResponse(access_token=token)


@router.get(
    "/users",
    response_model=list[schemas.UserAdminResponse],
    dependencies=[Depends(require_role("admin"))],
)
def list_users(db: Session = Depends(get_db)):
    """
    Возвращает список всех пользователей в системе.
    Доступно только администраторам.
    """
    return [_to_user_admin_response(user) for user in crud.get_users(db)]


@router.post(
    "/users/{user_id}/reset-password",
    response_model=schemas.UserAdminResponse,
    dependencies=[Depends(require_role("admin"))],
)
def reset_password(
    user_id: int,
    payload: schemas.UserPasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Административный сброс пароля пользователя.
    Не требует знания текущего пароля.
    """
    user = crud.reset_user_password(db, user_id, payload.new_password)
    return _to_user_admin_response(user)


@router.put(
    "/users/{user_id}",
    response_model=schemas.UserResponse,
    dependencies=[Depends(require_role("admin"))],
)
def update_user_account(
    user_id: int,
    payload: schemas.UserUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Административное обновление профиля пользователя.
    Позволяет изменять данные любого пользователя.
    """
    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = crud.update_user_account(db, user, payload)
    return _to_user_response(updated_user)


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_role("admin"))],
)
def delete_user_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Удаление пользователя из системы.
    Запрещено удалять собственный аккаунт.
    """
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    crud.delete_user(db, user_id)
    return {"message": "User deleted successfully"}
