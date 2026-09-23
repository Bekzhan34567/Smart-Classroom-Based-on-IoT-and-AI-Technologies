from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Student(Base):
    """
    Модель студента в системе.
    Связана с User через user_id для аутентификации.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)

    # ORM отношения
    attendance_records = relationship("Attendance", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    user = relationship("User", back_populates="student_profile", uselist=False)

    # Many-to-many отношение с Course через таблицу enrollments
    courses = relationship(
        "Course",
        secondary="enrollments",
        back_populates="students",
    )


class Teacher(Base):
    """
    Модель преподавателя.
    Преподаватель ведёт предметы и управляет курсами.
    """
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)

    # ORM отношения
    lectures = relationship("Lecture", back_populates="teacher")
    courses = relationship("Course", back_populates="teacher")
    user = relationship("User", back_populates="teacher_profile", uselist=False)


class Group(Base):
    """
    Модель учебной группы.
    Группы используются для организации студентов по специальностям/курсам.
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class Course(Base):
    """
    Модель учебного курса.
    Курс ведётся преподавателем и может быть назначен конкретной группе.
    """
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    group_name = Column(String, nullable=True)
    status = Column(String, default="active")
    join_code = Column(String, unique=True, index=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    # ORM отношения
    teacher = relationship("Teacher", back_populates="courses")
    lectures = relationship("Lecture", back_populates="course")

    # Many-to-many отношение со студентами через enrollments
    students = relationship(
        "Student",
        secondary="enrollments",
        back_populates="courses",
    )


class Lecture(Base):
    """
    Модель лекции/занятия.
    Лекция привязана к курсу и преподавателю, имеет расписание.
    """
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    duration = Column(Integer, default=80)
    room = Column(String)
    status = Column(String, default="scheduled")
    course_id = Column(Integer, ForeignKey("courses.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    # ORM отношения
    teacher = relationship("Teacher", back_populates="lectures")
    course = relationship("Course", back_populates="lectures")
    attendance_records = relationship("Attendance", back_populates="lecture")


class Attendance(Base):
    """
    Модель посещаемости.
    Записывает присутствие студента на конкретной лекции.
    UniqueConstraint гарантирует, что у студента только одна запись на лекцию.
    """
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    lecture_id = Column(Integer, ForeignKey("lectures.id"))
    status = Column(String, default="present")
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Гарантирует уникальность пары студент-лекция
    __table_args__ = (UniqueConstraint("student_id", "lecture_id"),)

    # ORM отношения
    student = relationship("Student", back_populates="attendance_records")
    lecture = relationship("Lecture", back_populates="attendance_records")


class Grade(Base):
    """
    Модель оценок студентов.
    Оценка привязана к студенту, курсу и предмету.
    course_id может быть NULL для старых записей (обратная совместимость).
    """
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    subject = Column(String, nullable=False)
    score = Column(Float, nullable=False)

    # ORM отношения
    student = relationship("Student", back_populates="grades")
    course = relationship("Course")


class User(Base):
    """
    Модель пользователя для аутентификации.
    Связана с Teacher или Student через user_id.
    Роль определяет права доступа в системе.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)

    # ORM отношения - один пользователь может быть либо преподавателем, либо студентом
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    student_profile = relationship("Student", back_populates="user", uselist=False)


class Enrollment(Base):
    """
    Промежуточная таблица для many-to-many отношения между Student и Course.
    Используется для записи студентов на курсы.
    UniqueConstraint предотвращает дублирование записей.
    """
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

    # Гарантирует, что студент может быть записан на курс только один раз
    __table_args__ = (UniqueConstraint("student_id", "course_id"),)
