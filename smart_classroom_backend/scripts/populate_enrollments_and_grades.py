"""
Скрипт для записи студентов на курсы и генерации случайных оценок
"""
import sys
import os
import random

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import crud, models

def populate_enrollments_and_grades():
    db: Session = SessionLocal()
    
    try:
        # Получаем всех студентов
        students = db.query(models.Student).all()
        print(f"Найдено студентов: {len(students)}")
        
        # Получаем все курсы
        courses = db.query(models.Course).all()
        print(f"Найдено курсов: {len(courses)}")
        
        # Записываем студентов на курсы
        enrollments_created = 0
        for student in students:
            for course in courses:
                # Проверяем, записан ли студент уже
                existing = db.query(models.Enrollment).filter(
                    models.Enrollment.student_id == student.id,
                    models.Enrollment.course_id == course.id
                ).first()
                
                if not existing:
                    enrollment = models.Enrollment(
                        student_id=student.id,
                        course_id=course.id
                    )
                    db.add(enrollment)
                    enrollments_created += 1
        
        db.commit()
        print(f"Создано записей на курсы: {enrollments_created}")
        
        # Получаем все лекции
        lectures = db.query(models.Lecture).all()
        print(f"Найдено лекций: {len(lectures)}")
        
        # Генерируем оценки для студентов
        grades_created = 0
        subjects = ["Математика", "Физика", "Программирование", "Базы данных", "Алгоритмы"]
        
        for student in students:
            for course in courses:
                # Генерируем 3-5 оценок на каждый курс
                num_grades = random.randint(3, 5)
                
                for _ in range(num_grades):
                    # Случайная оценка от 50 до 100 (с уклоном к высоким)
                    if random.random() < 0.3:  # 30% шанс на низкую оценку
                        score = random.randint(50, 70)
                    else:  # 70% шанс на высокую оценку
                        score = random.randint(70, 100)
                    
                    grade = models.Grade(
                        student_id=student.id,
                        course_id=course.id,
                        subject=random.choice(subjects),
                        score=score
                    )
                    db.add(grade)
                    grades_created += 1
        
        db.commit()
        print(f"Создано оценок: {grades_created}")
        
        # Генерируем посещаемость
        attendance_created = 0
        for student in students:
            for lecture in lectures:
                # Проверяем, существует ли запись
                existing = db.query(models.Attendance).filter(
                    models.Attendance.student_id == student.id,
                    models.Attendance.lecture_id == lecture.id
                ).first()
                
                if not existing:
                    # 80% шанс присутствия
                    if random.random() < 0.8:
                        attendance = models.Attendance(
                            student_id=student.id,
                            lecture_id=lecture.id,
                            status="present"
                        )
                    else:
                        attendance = models.Attendance(
                            student_id=student.id,
                            lecture_id=lecture.id,
                            status="absent"
                        )
                    db.add(attendance)
                    attendance_created += 1
        
        db.commit()
        print(f"Создано записей посещаемости: {attendance_created}")
        
        print("\n✅ Данные успешно заполнены!")
        print(f"- Студентов: {len(students)}")
        print(f"- Курсов: {len(courses)}")
        print(f"- Записей на курсы: {enrollments_created}")
        print(f"- Оценок: {grades_created}")
        print(f"- Посещаемости: {attendance_created}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_enrollments_and_grades()
