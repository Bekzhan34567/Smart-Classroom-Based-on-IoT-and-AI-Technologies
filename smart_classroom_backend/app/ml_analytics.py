"""
ML Analytics Module for Smart Classroom
Provides predictive analytics and AI-powered insights for educational management
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from . import models


class StudentPerformancePredictor:
    """
    ML модель для предсказания успеваемости студентов.
    Использует ансамбль методов: Gradient Boosting для оценок и Random Forest для рисков.
    """
    
    def __init__(self):
        # Gradient Boosting для регрессии (предсказание оценок)
        # n_estimators уменьшен для ускорения в демо-режиме
        self.grade_model = GradientBoostingRegressor(
            n_estimators=30,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        )
        
        # Random Forest для классификации (детекция рисков)
        self.risk_model = RandomForestClassifier(
            n_estimators=30,
            max_depth=5,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, student_data: List[Dict]) -> np.ndarray:
        """
        Подготавливает признаки для ML моделей из данных студентов.
        
        Признаки:
        - attendance_rate (нормализованный 0-1)
        - average_grade (нормализованный 0-1)
        - present_count (абсолютное значение)
        - absent_count (абсолютное значение)
        - total_attendance (абсолютное значение)
        """
        features = []
        for student in student_data:
            feature_vector = [
                student.get('attendance_rate', 0) / 100,  # Normalize to 0-1
                student.get('average_grade', 0) / 100,     # Normalize to 0-1
                student.get('present_count', 0),
                student.get('absent_count', 0),
                student.get('total_attendance', 0),
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def train_grade_model(self, X: np.ndarray, y: np.ndarray):
        """
        Обучает модель предсказания оценок (Gradient Boosting).
        Масштабирует признаки и обучает регрессор.
        """
        X_scaled = self.scaler.fit_transform(X)
        self.grade_model.fit(X_scaled, y)
        self.is_trained = True
    
    def train_risk_model(self, X: np.ndarray, y: np.ndarray):
        """
        Обучает модель детекции рисков (Random Forest).
        Классифицирует студентов на at-risk (1) и normal (0).
        """
        X_scaled = self.scaler.fit_transform(X)
        self.risk_model.fit(X_scaled, y)
        self.is_trained = True
    
    def predict_grade(self, features: np.ndarray) -> np.ndarray:
        """
        Предсказывает финальные оценки студентов.
        Если модель не обучена, возвращает дефолтное значение 70.0.
        Результаты ограничены диапазоном 0-100.
        """
        if not self.is_trained:
            return np.array([70.0] * len(features))  # Default prediction
        
        X_scaled = self.scaler.transform(features)
        predictions = self.grade_model.predict(X_scaled)
        return np.clip(predictions, 0, 100)
    
    def predict_risk(self, features: np.ndarray) -> np.ndarray:
        """
        Предсказывает статус риска студентов.
        Возвращает 1 для at-risk, 0 для normal.
        Если модель не обучена, возвращает 0 (no risk).
        """
        if not self.is_trained:
            return np.array([0] * len(features))  # Default: no risk
        
        X_scaled = self.scaler.transform(features)
        predictions = self.risk_model.predict(X_scaled)
        return predictions


class RecommendationEngine:
    """AI-powered recommendation system for students"""
    
    @staticmethod
    def generate_study_recommendations(
        attendance_rate: float,
        average_grade: float,
        absent_count: int,
        total_lectures: int
    ) -> List[str]:
        """Generate personalized study recommendations"""
        recommendations = []
        
        if attendance_rate < 70:
            recommendations.append(
                "Критически низкая посещаемость. Рекомендуется увеличить посещение занятий."
            )
        elif attendance_rate < 85:
            recommendations.append(
                "Посещаемость ниже оптимальной. Старайтесь не пропускать занятия."
            )
        
        if average_grade < 60:
            recommendations.append(
                "Академическая успеваемость требует внимания. Рекомендуются дополнительные занятия."
            )
        elif average_grade < 75:
            recommendations.append(
                "Есть потенциал для улучшения оценок. Уделите больше времени самоподготовке."
            )
        
        if absent_count > total_lectures * 0.3:
            recommendations.append(
                "Вы пропустили более 30% занятий. Это существенно влияет на успеваемость."
            )
        
        if attendance_rate > 90 and average_grade > 85:
            recommendations.append(
                "Отличные результаты! Рассмотрите возможность наставничества для других студентов."
            )
        
        if not recommendations:
            recommendations.append(
                "Хорошие показатели! Продолжайте в том же духе для поддержания успеваемости."
            )
        
        return recommendations
    
    @staticmethod
    def suggest_course_improvements(
        course_data: List[Dict]
    ) -> Dict[str, List[str]]:
        """Suggest improvements for courses based on performance data"""
        suggestions = {}
        
        for course in course_data:
            course_name = course.get('course_name', 'Unknown')
            avg_attendance = course.get('attendance_rate', 0)
            avg_grade = course.get('average_grade', 0)
            
            course_suggestions = []
            
            if avg_attendance < 70:
                course_suggestions.append(
                    "Рассмотрите пересмотр расписания или методики преподавания для повышения посещаемости."
                )
            
            if avg_grade < 60:
                course_suggestions.append(
                    "Студенты испытывают трудности с материалом. Рекомендуется дополнительное объяснение сложных тем."
                )
            
            if avg_grade > 85 and avg_attendance > 90:
                course_suggestions.append(
                    "Курс показывает отличные результаты. Можно рассмотреть углубление материала."
                )
            
            suggestions[course_name] = course_suggestions
        
        return suggestions


class AnomalyDetector:
    """Detect anomalous patterns in student behavior"""
    
    @staticmethod
    def detect_attendance_anomalies(
        student_attendance: List[float],
        threshold: float = 2.0
    ) -> List[int]:
        """Detect students with abnormal attendance patterns using z-score"""
        if len(student_attendance) < 3:
            return []
        
        mean = np.mean(student_attendance)
        std = np.std(student_attendance)
        
        if std == 0:
            return []
        
        z_scores = [(x - mean) / std for x in student_attendance]
        anomalies = [i for i, z in enumerate(z_scores) if abs(z) > threshold]
        
        return anomalies
    
    @staticmethod
    def detect_grade_anomalies(
        student_grades: List[float],
        threshold: float = 2.0
    ) -> List[int]:
        """Detect students with abnormal grade patterns"""
        if len(student_grades) < 3:
            return []
        
        mean = np.mean(student_grades)
        std = np.std(student_grades)
        
        if std == 0:
            return []
        
        z_scores = [(x - mean) / std for x in student_grades]
        anomalies = [i for i, z in enumerate(z_scores) if abs(z) > threshold]
        
        return anomalies
    
    @staticmethod
    def detect_sudden_performance_drop(
        grades_history: List[List[float]],
        threshold: float = 20.0
    ) -> List[int]:
        """Detect students with sudden performance drops"""
        students_with_drop = []
        
        for student_idx, grades in enumerate(grades_history):
            if len(grades) < 2:
                continue
            
            recent_avg = np.mean(grades[-3:]) if len(grades) >= 3 else grades[-1]
            earlier_avg = np.mean(grades[:-3]) if len(grades) >= 6 else np.mean(grades[:-1])
            
            if earlier_avg - recent_avg > threshold:
                students_with_drop.append(student_idx)
        
        return students_with_drop


def get_ml_predictions(db: Session) -> Dict:
    """Get ML-based predictions for all students"""
    from .analytics import get_student_summary
    
    students = db.query(models.Student).all()
    student_data = []
    
    for student in students:
        summary = get_student_summary(db, student.id)
        if summary:
            student_data.append({
                'student_id': student.id,
                'full_name': student.full_name,
                'attendance_rate': summary['attendance_rate'],
                'average_grade': summary['average_grade'],
                'present_count': summary['present_count'],
                'absent_count': summary['absent_count'],
                'total_attendance': summary['present_count'] + summary['absent_count'],
                'risk_status': summary['risk_status']
            })
    
    if not student_data:
        return {'predictions': [], 'recommendations': [], 'anomalies': []}
    
    # Initialize and train models
    predictor = StudentPerformancePredictor()
    
    # Prepare features
    features = predictor.prepare_features(student_data)
    
    # Create synthetic training data (in real scenario, use historical data)
    X_train = features
    y_grade = np.array([s['average_grade'] for s in student_data])
    y_risk = np.array([1 if s['risk_status'] == 'At Risk' else 0 for s in student_data])
    
    # Train models
    predictor.train_grade_model(X_train, y_grade)
    predictor.train_risk_model(X_train, y_risk)
    
    # Make predictions
    predicted_grades = predictor.predict_grade(features)
    predicted_risks = predictor.predict_risk(features)
    
    # Generate recommendations
    recommender = RecommendationEngine()
    recommendations = []
    
    for i, student in enumerate(student_data):
        student_recs = recommender.generate_study_recommendations(
            student['attendance_rate'],
            student['average_grade'],
            student['absent_count'],
            student['total_attendance']
        )
        recommendations.append({
            'student_id': student['student_id'],
            'full_name': student['full_name'],
            'recommendations': student_recs
        })
    
    # Detect anomalies
    detector = AnomalyDetector()
    attendance_rates = [s['attendance_rate'] for s in student_data]
    grade_averages = [s['average_grade'] for s in student_data]
    
    attendance_anomalies = detector.detect_attendance_anomalies(attendance_rates)
    grade_anomalies = detector.detect_grade_anomalies(grade_averages)
    
    anomalies = []
    for idx in set(attendance_anomalies + grade_anomalies):
        anomalies.append({
            'student_id': student_data[idx]['student_id'],
            'full_name': student_data[idx]['full_name'],
            'type': 'attendance' if idx in attendance_anomalies else 'grade',
            'value': attendance_rates[idx] if idx in attendance_anomalies else grade_averages[idx]
        })
    
    # Combine results
    predictions = []
    for i, student in enumerate(student_data):
        predictions.append({
            'student_id': student['student_id'],
            'full_name': student['full_name'],
            'current_grade': student['average_grade'],
            'predicted_grade': round(predicted_grades[i], 2),
            'predicted_risk': bool(predicted_risks[i]),
            'confidence': 0.85  # Placeholder confidence score
        })
    
    return {
        'predictions': predictions,
        'recommendations': recommendations,
        'anomalies': anomalies
    }


def get_course_recommendations(db: Session) -> Dict:
    """Get AI-powered recommendations for courses"""
    from .analytics import get_progress_report
    
    courses = db.query(models.Course).all()
    course_data = []
    
    for course in courses:
        report = get_progress_report(db, course_id=course.id)
        if report:
            avg_attendance = np.mean([r['attendance_rate'] for r in report]) if report else 0
            avg_grade = np.mean([r['average_grade'] for r in report]) if report else 0
            
            course_data.append({
                'course_id': course.id,
                'course_name': course.name,
                'attendance_rate': avg_attendance,
                'average_grade': avg_grade
            })
    
    recommender = RecommendationEngine()
    suggestions = recommender.suggest_course_improvements(course_data)
    
    return {
        'course_suggestions': suggestions,
        'total_courses': len(course_data)
    }
