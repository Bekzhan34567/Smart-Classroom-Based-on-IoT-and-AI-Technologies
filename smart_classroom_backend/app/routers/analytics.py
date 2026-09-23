from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..analytics import get_at_risk_students, get_progress_report, get_student_summary
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/at-risk-students", dependencies=[Depends(require_role("admin", "teacher"))])
def at_risk_students(db: Session = Depends(get_db), user=Depends(get_current_user)):
    results = get_at_risk_students(db)
    if user.role.lower() == "teacher":
        allowed_ids = {student.id for student in crud.get_students_for_user(db, user)}
        return [item for item in results if item["student_id"] in allowed_ids]
    return results


@router.get("/student-summary/{student_id}")
def student_summary(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role.lower() == "student":
        if user.student_profile is None or user.student_profile.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
    elif user.role.lower() not in {"admin", "teacher"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    elif user.role.lower() == "teacher":
        teacher_students = crud.get_students_for_user(db, user)
        allowed_ids = {student.id for student in teacher_students}
        if student_id not in allowed_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )

    summary = get_student_summary(db, student_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Student not found")
    return summary


@router.get("/report", dependencies=[Depends(require_role("admin", "teacher"))])
def progress_report(
    group_name: str | None = None,
    course_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role.lower() == "teacher" and course_id is not None:
        teacher_courses = {course.id for course in crud.get_courses_for_user(db, user)}
        if course_id not in teacher_courses:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    report_rows = get_progress_report(db, group_name=group_name, course_id=course_id)

    if user.role.lower() == "teacher":
        allowed_ids = {student.id for student in crud.get_students_for_user(db, user)}
        report_rows = [row for row in report_rows if row["student_id"] in allowed_ids]

    return report_rows
