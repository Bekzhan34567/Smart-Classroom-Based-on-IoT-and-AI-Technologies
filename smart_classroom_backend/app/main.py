from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models
from .auth_utils import hash_password
from .database import Base, engine, SessionLocal
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
def create_default_superadmin():
    db = SessionLocal()
    try:
        email = "superadmin@smartclassroom.edu"

        existing_user = (
            db.query(models.User)
            .filter(models.User.email == email)
            .first()
        )

        if existing_user is not None:
            return

        superadmin = models.User(
            full_name="Super Administrator",
            email=email,
            password=hash_password("SuperAdmin123!"),
            role="admin",
            is_superuser=1,
        )

        db.add(superadmin)
        db.commit()

        print("Default superadmin created")

    finally:
        db.close()

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

def create_demo_data():
    db = SessionLocal()

    try:
        # =========================
        # 1. Группа
        # =========================
        group = db.query(models.Group).filter(
            models.Group.name == "10A"
        ).first()

        if group is None:
            group = models.Group(name="10A")
            db.add(group)
            db.commit()
            db.refresh(group)

        # =========================
        # 2. Преподаватель 1
        # =========================
        teacher1_email = "math.teacher@smartclassroom.edu"

        teacher1_user = db.query(models.User).filter(
            models.User.email == teacher1_email
        ).first()

        if teacher1_user is None:
            teacher1_user = models.User(
                full_name="Иван Петров",
                email=teacher1_email,
                password=hash_password("Teacher123!"),
                role="teacher",
                is_superuser=0,
            )
            db.add(teacher1_user)
            db.commit()
            db.refresh(teacher1_user)

        teacher1 = db.query(models.Teacher).filter(
            models.Teacher.email == teacher1_email
        ).first()

        if teacher1 is None:
            teacher1 = models.Teacher(
                full_name="Иван Петров",
                subject="Математика",
                email=teacher1_email,
                user_id=teacher1_user.id,
            )
            db.add(teacher1)
            db.commit()
            db.refresh(teacher1)

        # =========================
        # 3. Преподаватель 2
        # =========================
        teacher2_email = "programming.teacher@smartclassroom.edu"

        teacher2_user = db.query(models.User).filter(
            models.User.email == teacher2_email
        ).first()

        if teacher2_user is None:
            teacher2_user = models.User(
                full_name="Александр Сидоров",
                email=teacher2_email,
                password=hash_password("Teacher123!"),
                role="teacher",
                is_superuser=0,
            )
            db.add(teacher2_user)
            db.commit()
            db.refresh(teacher2_user)

        teacher2 = db.query(models.Teacher).filter(
            models.Teacher.email == teacher2_email
        ).first()

        if teacher2 is None:
            teacher2 = models.Teacher(
                full_name="Александр Сидоров",
                subject="Программирование",
                email=teacher2_email,
                user_id=teacher2_user.id,
            )
            db.add(teacher2)
            db.commit()
            db.refresh(teacher2)

        # =========================
        # 4. Студент 1
        # =========================
        student1_email = "student1@smartclassroom.edu"

        student1_user = db.query(models.User).filter(
            models.User.email == student1_email
        ).first()

        if student1_user is None:
            student1_user = models.User(
                full_name="Алексей Иванов",
                email=student1_email,
                password=hash_password("Student123!"),
                role="student",
                is_superuser=0,
            )
            db.add(student1_user)
            db.commit()
            db.refresh(student1_user)

        student1 = db.query(models.Student).filter(
            models.Student.email == student1_email
        ).first()

        if student1 is None:
            student1 = models.Student(
                full_name="Алексей Иванов",
                group_name="10A",
                email=student1_email,
                user_id=student1_user.id,
            )
            db.add(student1)
            db.commit()
            db.refresh(student1)

        # =========================
        # 5. Студент 2
        # =========================
        student2_email = "student2@smartclassroom.edu"

        student2_user = db.query(models.User).filter(
            models.User.email == student2_email
        ).first()

        if student2_user is None:
            student2_user = models.User(
                full_name="Мария Смирнова",
                email=student2_email,
                password=hash_password("Student123!"),
                role="student",
                is_superuser=0,
            )
            db.add(student2_user)
            db.commit()
            db.refresh(student2_user)

        student2 = db.query(models.Student).filter(
            models.Student.email == student2_email
        ).first()

        if student2 is None:
            student2 = models.Student(
                full_name="Мария Смирнова",
                group_name="10A",
                email=student2_email,
                user_id=student2_user.id,
            )
            db.add(student2)
            db.commit()
            db.refresh(student2)

        # =========================
        # 6. Курс 1
        # =========================
        course1 = db.query(models.Course).filter(
            models.Course.name == "Математика"
        ).first()

        if course1 is None:
            course1 = models.Course(
                name="Математика",
                group_name="10A",
                status="active",
                join_code="MATH10A",
                teacher_id=teacher1.id,
            )
            db.add(course1)
            db.commit()
            db.refresh(course1)

        # =========================
        # 7. Курс 2
        # =========================
        course2 = db.query(models.Course).filter(
            models.Course.name == "Программирование"
        ).first()

        if course2 is None:
            course2 = models.Course(
                name="Программирование",
                group_name="10A",
                status="active",
                join_code="PROG10A",
                teacher_id=teacher2.id,
            )
            db.add(course2)
            db.commit()
            db.refresh(course2)

        # =========================
        # 8. Студент 1 → курс 1
        # =========================
        if not db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student1.id,
            models.Enrollment.course_id == course1.id,
        ).first():
            db.add(models.Enrollment(
                student_id=student1.id,
                course_id=course1.id,
            ))

        # Студент 1 → курс 2
        if not db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student1.id,
            models.Enrollment.course_id == course2.id,
        ).first():
            db.add(models.Enrollment(
                student_id=student1.id,
                course_id=course2.id,
            ))

        # =========================
        # 9. Студент 2 → курс 1
        # =========================
        if not db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student2.id,
            models.Enrollment.course_id == course1.id,
        ).first():
            db.add(models.Enrollment(
                student_id=student2.id,
                course_id=course1.id,
            ))

        # Студент 2 → курс 2
        if not db.query(models.Enrollment).filter(
            models.Enrollment.student_id == student2.id,
            models.Enrollment.course_id == course2.id,
        ).first():
            db.add(models.Enrollment(
                student_id=student2.id,
                course_id=course2.id,
            ))

        db.commit()

        print("Demo data created successfully")

    finally:
        db.close()


run_legacy_sqlite_migrations()
Base.metadata.create_all(bind=engine)
backfill_course_join_codes()
create_default_superadmin()
create_demo_data()

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
