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
        # ==========================================
        # 1. ГРУППА
        # ==========================================
        group = db.query(models.Group).filter(
            models.Group.name == "10A"
        ).first()

        if group is None:
            group = models.Group(name="10A")
            db.add(group)
            db.commit()
            db.refresh(group)

        # ==========================================
        # 2. ПРЕПОДАВАТЕЛЬ 1
        # ==========================================
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

        # ==========================================
        # 3. ПРЕПОДАВАТЕЛЬ 2
        # ==========================================
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

        # ==========================================
        # 4. СТУДЕНТ 1
        # ==========================================
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

        # ==========================================
        # 5. СТУДЕНТ 2
        # ==========================================
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

        # ==========================================
        # 6. КУРС 1
        # ==========================================
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

        # ==========================================
        # 7. КУРС 2
        # ==========================================
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

        # ==========================================
        # 8. ЗАПИСЬ СТУДЕНТОВ НА КУРСЫ
        # ==========================================
        enrollments = [
            (student1.id, course1.id),
            (student1.id, course2.id),
            (student2.id, course1.id),
            (student2.id, course2.id),
        ]

        for student_id, course_id in enrollments:
            exists = db.query(models.Enrollment).filter(
                models.Enrollment.student_id == student_id,
                models.Enrollment.course_id == course_id,
            ).first()

            if exists is None:
                db.add(models.Enrollment(
                    student_id=student_id,
                    course_id=course_id,
                ))

        db.commit()

        # ==========================================
        # 9. ЛЕКЦИИ
        # ==========================================
        # 5 и 6 октября 2026 года — понедельник и вторник.
        # 7 и 8 октября — среда и четверг.

        lecture_data = [
            {
                "title": "Основы математики",
                "subject": "Математика",
                "date": date(2026, 10, 5),
                "time": time(9, 0),
                "duration": 80,
                "room": "101",
                "status": "completed",
                "course_id": course1.id,
                "teacher_id": teacher1.id,
            },
            {
                "title": "Алгебра и функции",
                "subject": "Математика",
                "date": date(2026, 10, 7),
                "time": time(9, 0),
                "duration": 80,
                "room": "101",
                "status": "completed",
                "course_id": course1.id,
                "teacher_id": teacher1.id,
            },
            {
                "title": "Введение в программирование",
                "subject": "Программирование",
                "date": date(2026, 10, 6),
                "time": time(10, 30),
                "duration": 80,
                "room": "202",
                "status": "completed",
                "course_id": course2.id,
                "teacher_id": teacher2.id,
            },
            {
                "title": "Основы Python",
                "subject": "Программирование",
                "date": date(2026, 10, 8),
                "time": time(10, 30),
                "duration": 80,
                "room": "202",
                "status": "completed",
                "course_id": course2.id,
                "teacher_id": teacher2.id,
            },
        ]

        lectures = []

        for data in lecture_data:
            lecture = db.query(models.Lecture).filter(
                models.Lecture.title == data["title"],
                models.Lecture.course_id == data["course_id"],
            ).first()

            if lecture is None:
                lecture = models.Lecture(**data)
                db.add(lecture)
                db.commit()
                db.refresh(lecture)

            lectures.append(lecture)

        # ==========================================
        # 10. ПОСЕЩАЕМОСТЬ
        # ==========================================
        attendance_data = [
            # Математика — лекция 1
            (student1.id, lectures[0].id, "present"),
            (student2.id, lectures[0].id, "late"),

            # Математика — лекция 2
            (student1.id, lectures[1].id, "present"),
            (student2.id, lectures[1].id, "absent"),

            # Программирование — лекция 1
            (student1.id, lectures[2].id, "present"),
            (student2.id, lectures[2].id, "present"),

            # Программирование — лекция 2
            (student1.id, lectures[3].id, "late"),
            (student2.id, lectures[3].id, "present"),
        ]

        for student_id, lecture_id, attendance_status in attendance_data:
            record = db.query(models.Attendance).filter(
                models.Attendance.student_id == student_id,
                models.Attendance.lecture_id == lecture_id,
            ).first()

            if record is None:
                record = models.Attendance(
                    student_id=student_id,
                    lecture_id=lecture_id,
                    status=attendance_status,
                )
                db.add(record)

        db.commit()

        # ==========================================
        # 11. ОЦЕНКИ
        # ==========================================
        grade_data = [
            # Алексей — Математика
            (student1.id, course1.id, "Математика", 90),
            (student1.id, course1.id, "Математика", 85),

            # Алексей — Программирование
            (student1.id, course2.id, "Программирование", 95),
            (student1.id, course2.id, "Программирование", 88),

            # Мария — Математика
            (student2.id, course1.id, "Математика", 78),
            (student2.id, course1.id, "Математика", 92),

            # Мария — Программирование
            (student2.id, course2.id, "Программирование", 84),
            (student2.id, course2.id, "Программирование", 91),
        ]

        for student_id, course_id, subject, score in grade_data:
            exists = db.query(models.Grade).filter(
                models.Grade.student_id == student_id,
                models.Grade.course_id == course_id,
                models.Grade.subject == subject,
                models.Grade.score == score,
            ).first()

            if exists is None:
                db.add(models.Grade(
                    student_id=student_id,
                    course_id=course_id,
                    subject=subject,
                    score=score,
                ))

        db.commit()

        print("Demo data with courses, lectures, attendance and grades created successfully")

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
