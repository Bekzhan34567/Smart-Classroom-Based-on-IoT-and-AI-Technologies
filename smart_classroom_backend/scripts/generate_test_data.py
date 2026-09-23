"""
Generate test data for Smart Classroom
Creates 30 students, 7 teachers, 2 admins, groups, courses, lectures, attendance, and grades
"""

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import engine, Base
from app import models
from app.course_codes import generate_join_code
from app.auth_utils import hash_password


# Test data
GROUPS = ["ИТ-21", "ИТ-22", "ИТ-23", "МК-21", "МК-22"]
SUBJECTS = ["Математика", "Программирование", "Базы данных", "Алгоритмы", "Веб-разработка", "Мобильная разработка", "Машинное обучение"]
FIRST_NAMES = ["Александр", "Максим", "Артем", "Дмитрий", "Никита", "Михаил", "Иван", "Даниил", "Андрей", "Сергей"]
LAST_NAMES = ["Иванов", "Петров", "Сидоров", "Козлов", "Новиков", "Морозов", "Волков", "Соколов", "Лебедев", "Кузнецов"]
MIDDLE_NAMES = ["Александрович", "Максимович", "Артемович", "Дмитриевич", "Никитич", "Михайлович", "Иванович", "Даниилович", "Андреевич", "Сергеевич"]


def generate_full_name():
    """Generate random Russian full name"""
    return f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)} {random.choice(MIDDLE_NAMES)}"


def generate_email(full_name: str, index: int) -> str:
    """Generate unique email from full name"""
    last_name, first_name = full_name.split()[:2]
    return f"{first_name.lower()}.{last_name.lower()}{index}@university.edu"


def generate_test_data():
    """Generate comprehensive test data"""
    
    # Drop and recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as session:
        print("🔧 Создание групп...")
        # Create groups
        groups = []
        for group_name in GROUPS:
            group = models.Group(name=group_name)
            session.add(group)
            groups.append(group)
        session.flush()
        
        print("👨‍🏫 Создание 7 преподавателей...")
        # Create 7 teachers
        teachers = []
        for i, subject in enumerate(SUBJECTS[:7]):
            teacher = models.Teacher(
                full_name=f"Преподаватель {subject}",
                subject=subject,
                email=f"teacher.{i}@university.edu"
            )
            session.add(teacher)
            teachers.append(teacher)
        session.flush()
        
        print("👨‍🎓 Создание 30 студентов...")
        # Create 30 students distributed across groups
        students = []
        for i in range(30):
            group = random.choice(groups)
            full_name = generate_full_name()
            student = models.Student(
                full_name=full_name,
                group_name=group.name,
                email=generate_email(full_name, i)
            )
            session.add(student)
            students.append(student)
        session.flush()

        print("👤 Создание пользователей с известными паролями...")
        # Create users with known passwords
        test_password = hash_password("password123")
        
        # Create 7 teacher users
        for i, teacher in enumerate(teachers):
            user = models.User(
                email=f"teacher.{i}@university.edu",
                password=test_password,
                full_name=teacher.full_name,
                role="teacher"
            )
            session.add(user)
            session.flush()
            teacher.user_id = user.id
        
        # Create 30 student users
        for i, student in enumerate(students):
            user = models.User(
                email=student.email,
                password=test_password,
                full_name=student.full_name,
                role="student"
            )
            session.add(user)
            session.flush()
            student.user_id = user.id
        
        # Create 2 admin users
        admin1 = models.User(
            email="admin1@university.edu",
            password=test_password,
            full_name="Администратор 1",
            role="admin"
        )
        session.add(admin1)
        
        admin2 = models.User(
            email="admin2@university.edu",
            password=test_password,
            full_name="Администратор 2",
            role="admin"
        )
        session.add(admin2)
        session.flush()
        
        print("📚 Создание курсов...")
        # Create courses for each teacher
        courses = []
        existing_codes = set()
        for teacher in teachers:
            for group in groups:  # Each teacher teaches all 5 groups
                join_code = generate_join_code()
                while join_code in existing_codes:
                    join_code = generate_join_code()
                existing_codes.add(join_code)
                
                course = models.Course(
                    name=f"{teacher.subject} ({group.name})",
                    group_name=group.name,
                    teacher_id=teacher.id,
                    status="active",
                    join_code=join_code
                )
                session.add(course)
                courses.append(course)
        session.flush()
        
        print("📝 Создание записей студентов на курсы...")
        # Enroll students in courses
        for student in students:
            # Each student takes 3-5 courses
            student_courses = random.sample(courses, random.randint(3, 5))
            for course in student_courses:
                if course.group_name == student.group_name:
                    enrollment = models.Enrollment(
                        student_id=student.id,
                        course_id=course.id
                    )
                    session.add(enrollment)
        session.flush()
        
        print("📅 Создание лекций...")
        # Create lectures for each course
        lectures = []
        start_date = datetime.now() - timedelta(days=60)
        
        for course in courses:
            # Create 8-12 lectures per course
            num_lectures = random.randint(8, 12)
            for i in range(num_lectures):
                lecture_date = start_date + timedelta(days=i * 7)  # Weekly lectures
                # Get subject from course name or teacher
                subject = course.name.split('(')[0].strip()
                lecture = models.Lecture(
                    title=f"{subject} - Лекция {i+1}",
                    subject=subject,
                    date=lecture_date.date(),
                    time=datetime.now().time(),
                    duration=random.choice([60, 80, 90]),
                    room=f"Кабинет {random.randint(101, 305)}",
                    status="completed" if lecture_date < datetime.now() else "scheduled",
                    course_id=course.id,
                    teacher_id=course.teacher_id
                )
                session.add(lecture)
                lectures.append(lecture)
        session.flush()
        
        print("✅ Создание записей посещаемости...")
        # Create attendance records
        for student in students:
            student_lectures = session.query(models.Lecture).join(
                models.Course, models.Lecture.course_id == models.Course.id
            ).join(
                models.Enrollment, models.Course.id == models.Enrollment.course_id
            ).filter(
                models.Enrollment.student_id == student.id
            ).all()
            
            for lecture in student_lectures:
                # Random attendance: 70% present, 20% absent, 10% late
                rand = random.random()
                if rand < 0.7:
                    status = "present"
                elif rand < 0.9:
                    status = "absent"
                else:
                    status = "late"
                
                attendance = models.Attendance(
                    student_id=student.id,
                    lecture_id=lecture.id,
                    status=status,
                    timestamp=datetime.now() - timedelta(days=random.randint(1, 60))
                )
                session.add(attendance)
        session.flush()
        
        print("📊 Создание оценок...")
        # Create grades for students
        for student in students:
            student_courses = session.query(models.Course).join(
                models.Enrollment, models.Course.id == models.Enrollment.course_id
            ).filter(
                models.Enrollment.student_id == student.id
            ).all()
            
            for course in student_courses:
                # Create 3-5 grades per course
                num_grades = random.randint(3, 5)
                for _ in range(num_grades):
                    grade = models.Grade(
                        student_id=student.id,
                        course_id=course.id,
                        subject=course.name,
                        score=random.uniform(30, 100)  # Random grade between 30 and 100
                    )
                    session.add(grade)
        session.flush()
        
        session.commit()
        
        print("\n✅ Тестовые данные успешно созданы!")
        print(f"📊 Статистика:")
        print(f"   - Групп: {len(groups)}")
        print(f"   - Преподавателей: {len(teachers)}")
        print(f"   - Студентов: {len(students)}")
        print(f"   - Курсов: {len(courses)}")
        print(f"   - Лекций: {len(lectures)}")
        
        # Count attendance and grades
        attendance_count = session.query(models.Attendance).count()
        grades_count = session.query(models.Grade).count()
        enrollments_count = session.query(models.Enrollment).count()
        
        print(f"   - Записей на курсы: {enrollments_count}")
        print(f"   - Записей посещаемости: {attendance_count}")
        print(f"   - Оценок: {grades_count}")


if __name__ == "__main__":
    generate_test_data()
