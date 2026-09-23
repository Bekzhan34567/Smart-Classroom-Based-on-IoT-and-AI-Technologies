from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models
from .database import Base, engine
from .routers import (
    analytics,
    attendance,
    auth,
    courses,
    enrollments,
    groups,
    grades,
    iot,
    lectures,
    ml_analytics,
    students,
    teachers,
)


def run_legacy_sqlite_migrations():
    """
    Миграция для добавления новых колонок в существующую SQLite базу.
    SQLite не поддерживает ALTER TABLE в полном объёме, поэтому добавляем колонки вручную.
    try-except нужен для пропуска ошибок, если колонки уже существуют.
    """
    statements = [
        "ALTER TABLE students ADD COLUMN user_id INTEGER",
        "ALTER TABLE teachers ADD COLUMN user_id INTEGER",
        "ALTER TABLE courses ADD COLUMN status TEXT DEFAULT 'active'",
        "ALTER TABLE courses ADD COLUMN join_code TEXT",
        "ALTER TABLE courses ADD COLUMN group_name TEXT",
        "ALTER TABLE grades ADD COLUMN course_id INTEGER",
    ]

    with engine.begin() as connection:
        for statement in statements:
            try:
                connection.execute(text(statement))
            except Exception:
                pass


def backfill_course_join_codes():
    """
    Генерация уникальных кодов для записи на курсы, которые были созданы без кодов.
    Коды нужны для self-enroll функционала.
    """
    from .course_codes import generate_join_code

    with Session(engine) as session:
        courses_without_code = session.query(models.Course).filter(models.Course.join_code.is_(None)).all()
        existing_codes = {
            code for (code,) in session.query(models.Course.join_code).filter(models.Course.join_code.is_not(None)).all()
        }
        changed = False

        for course in courses_without_code:
            join_code = generate_join_code()
            while join_code in existing_codes:
                join_code = generate_join_code()
            course.join_code = join_code
            existing_codes.add(join_code)
            changed = True

        if changed:
            session.commit()


# Запуск миграций и создание таблиц при старте приложения
run_legacy_sqlite_migrations()
Base.metadata.create_all(bind=engine)
backfill_course_join_codes()

app = FastAPI(title="Smart Classroom Backend System")

# CORS middleware для разрешения запросов с фронтенда
# В продакшене нужно ограничить allow_origins конкретными доменами
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров - порядок важен для маршрутизации
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(courses.router)
app.include_router(enrollments.router)
app.include_router(lectures.router)
app.include_router(attendance.router)
app.include_router(grades.router)
app.include_router(analytics.router)
app.include_router(ml_analytics.router)
app.include_router(iot.router)


@app.get("/")
def root():
    return {"message": "Smart Classroom Backend is running"}
