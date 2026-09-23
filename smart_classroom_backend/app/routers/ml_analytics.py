"""
ML Analytics API Endpoints
Provides AI-powered insights and predictions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_role
from ..ml_analytics import get_ml_predictions, get_course_recommendations

router = APIRouter(prefix="/ml-analytics", tags=["ML Analytics"])


@router.get("/predictions", dependencies=[Depends(get_current_user)])
def get_student_predictions(db: Session = Depends(get_db)):
    """
    Get ML-based predictions for all students
    Includes grade predictions, risk assessment, and confidence scores
    """
    try:
        predictions = get_ml_predictions(db)
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")


@router.get("/predictions/{student_id}", dependencies=[Depends(get_current_user)])
def get_student_prediction(student_id: int, db: Session = Depends(get_db)):
    """
    Get ML-based prediction for a specific student
    """
    try:
        predictions = get_ml_predictions(db)
        student_prediction = next(
            (p for p in predictions['predictions'] if p['student_id'] == student_id),
            None
        )
        
        if not student_prediction:
            raise HTTPException(status_code=404, detail="Student not found")
        
        student_recommendations = next(
            (r for r in predictions['recommendations'] if r['student_id'] == student_id),
            {'recommendations': []}
        )
        
        return {
            'prediction': student_prediction,
            'recommendations': student_recommendations['recommendations']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prediction: {str(e)}")


@router.get("/recommendations/courses", dependencies=[Depends(require_role("admin", "teacher"))])
def get_course_recommendations_endpoint(db: Session = Depends(get_db)):
    """
    Get AI-powered recommendations for course improvements
    """
    try:
        recommendations = get_course_recommendations(db)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


@router.get("/anomalies", dependencies=[Depends(require_role("admin", "teacher"))])
def get_behavior_anomalies(db: Session = Depends(get_db)):
    """
    Get detected anomalies in student behavior
    """
    try:
        predictions = get_ml_predictions(db)
        return {
            'anomalies': predictions['anomalies'],
            'total_anomalies': len(predictions['anomalies'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@router.get("/summary", dependencies=[Depends(get_current_user)])
def get_ml_summary(db: Session = Depends(get_db)):
    """
    Get comprehensive ML analytics summary
    """
    try:
        predictions = get_ml_predictions(db)
        course_recs = get_course_recommendations(db)
        
        at_risk_count = sum(1 for p in predictions['predictions'] if p['predicted_risk'])
        total_students = len(predictions['predictions'])
        
        avg_predicted_grade = sum(p['predicted_grade'] for p in predictions['predictions']) / total_students if total_students > 0 else 0
        
        return {
            'overview': {
                'total_students': total_students,
                'students_at_risk': at_risk_count,
                'risk_percentage': round((at_risk_count / total_students * 100) if total_students > 0 else 0, 2),
                'average_predicted_grade': round(avg_predicted_grade, 2),
                'total_anomalies': len(predictions['anomalies']),
                'total_courses': course_recs['total_courses']
            },
            'predictions': predictions['predictions'][:10],  # Return top 10 for summary
            'anomalies': predictions['anomalies'],
            'course_recommendations': course_recs['course_suggestions']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")
