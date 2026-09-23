from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from . import models


def _student_metrics_subquery(db: Session):
    attendance_metrics = (
        db.query(
            models.Attendance.student_id.label("student_id"),
            func.count(models.Attendance.id).label("total_attendance"),
            func.sum(
                case((models.Attendance.status == "present", 1), else_=0)
            ).label("present_count"),
            func.sum(
                case((models.Attendance.status == "absent", 1), else_=0)
            ).label("absent_count"),
        )
        .group_by(models.Attendance.student_id)
        .subquery()
    )

    grade_metrics = (
        db.query(
            models.Grade.student_id.label("student_id"),
            func.avg(models.Grade.score).label("average_grade"),
        )
        .group_by(models.Grade.student_id)
        .subquery()
    )

    return (
        db.query(
            models.Student.id.label("student_id"),
            models.Student.full_name.label("full_name"),
            models.Student.group_name.label("group_name"),
            attendance_metrics.c.total_attendance.label("total_attendance"),
            attendance_metrics.c.present_count.label("present_count"),
            attendance_metrics.c.absent_count.label("absent_count"),
            grade_metrics.c.average_grade.label("average_grade"),
        )
        .select_from(models.Student)
        .outerjoin(attendance_metrics, attendance_metrics.c.student_id == models.Student.id)
        .outerjoin(grade_metrics, grade_metrics.c.student_id == models.Student.id)
        .subquery()
    )


def _build_summary_from_row(row):
    total_attendance = int(row.total_attendance or 0)
    present_count = int(row.present_count or 0)
    absent_count = int(row.absent_count or 0)
    average_grade = float(row.average_grade or 0)

    attendance_rate = 100.0 if total_attendance == 0 else (present_count / total_attendance) * 100
    final_score = (average_grade * 0.9) + (attendance_rate * 0.1)
    risk_status = "At Risk" if attendance_rate < 70 or average_grade < 60 else "Normal"

    return {
        "student_id": row.student_id,
        "full_name": row.full_name,
        "group_name": row.group_name,
        "attendance_rate": round(attendance_rate, 2),
        "present_count": present_count,
        "absent_count": absent_count,
        "average_grade": round(average_grade, 2),
        "final_score": round(final_score, 2),
        "risk_status": risk_status,
    }


def get_student_course_results(db: Session, student_id: int):
    enrolled_courses = (
        db.query(models.Course)
        .join(models.Enrollment, models.Enrollment.course_id == models.Course.id)
        .filter(models.Enrollment.student_id == student_id)
        .order_by(models.Course.name.asc())
        .all()
    )

    results = []
    for course in enrolled_courses:
        lectures = (
            db.query(models.Lecture)
            .filter(models.Lecture.course_id == course.id)
            .all()
        )
        lecture_ids = [lecture.id for lecture in lectures]
        subject = lectures[0].subject if lectures else course.name

        attendance_rows = []
        if lecture_ids:
            attendance_rows = (
                db.query(models.Attendance)
                .filter(
                    models.Attendance.student_id == student_id,
                    models.Attendance.lecture_id.in_(lecture_ids),
                )
                .all()
            )

        total_attendance = len(attendance_rows)
        present_count = sum(1 for row in attendance_rows if row.status == "present")
        absent_count = sum(1 for row in attendance_rows if row.status == "absent")
        attendance_rate = 100.0 if total_attendance == 0 else (present_count / total_attendance) * 100

        grade_rows = (
            db.query(models.Grade)
            .filter(
                models.Grade.student_id == student_id,
                or_(
                    models.Grade.course_id == course.id,
                    and_(
                        models.Grade.course_id.is_(None),
                        models.Grade.subject == subject,
                    ),
                ),
            )
            .all()
        )
        average_grade = sum(row.score for row in grade_rows) / len(grade_rows) if grade_rows else 0.0
        final_score = (average_grade * 0.9) + (attendance_rate * 0.1)
        risk_status = "At Risk" if attendance_rate < 70 or average_grade < 60 else "Normal"

        results.append(
            {
                "course_id": course.id,
                "course_name": course.name,
                "subject": subject,
                "attendance_rate": round(attendance_rate, 2),
                "present_count": present_count,
                "absent_count": absent_count,
                "average_grade": round(average_grade, 2),
                "final_score": round(final_score, 2),
                "risk_status": risk_status,
            }
        )

    return results


def get_at_risk_students(db: Session):
    metrics_subquery = _student_metrics_subquery(db)
    metrics = db.query(*metrics_subquery.c).all()
    results = []

    for row in metrics:
        summary = _build_summary_from_row(row)
        if summary["risk_status"] == "At Risk":
            results.append(
                {
                    "student_id": summary["student_id"],
                    "full_name": summary["full_name"],
                    "attendance_rate": summary["attendance_rate"],
                    "average_grade": summary["average_grade"],
                    "final_score": summary["final_score"],
                }
            )

    return results


def get_student_summary(db: Session, student_id: int):
    metrics_subquery = _student_metrics_subquery(db)
    row = (
        db.query(*metrics_subquery.c)
        .filter(metrics_subquery.c.student_id == student_id)
        .first()
    )

    if row is None:
        return None

    summary = _build_summary_from_row(row)
    summary["course_results"] = get_student_course_results(db, student_id)
    return summary


def get_progress_report(db: Session, group_name: str | None = None, course_id: int | None = None):
    students_query = db.query(models.Student)

    if group_name:
        students_query = students_query.filter(models.Student.group_name == group_name)

    if course_id is not None:
        students_query = (
            students_query
            .join(models.Enrollment, models.Enrollment.student_id == models.Student.id)
            .filter(models.Enrollment.course_id == course_id)
        )

    students = students_query.distinct().order_by(models.Student.full_name.asc()).all()
    report_rows = []

    selected_course = None
    if course_id is not None:
        selected_course = db.query(models.Course).filter(models.Course.id == course_id).first()

    for student in students:
        summary = get_student_summary(db, student.id)
        if not summary:
            continue

        if course_id is not None:
            course_result = next(
                (item for item in summary["course_results"] if item["course_id"] == course_id),
                None,
            )
            if course_result is None:
                continue
            report_rows.append(
                {
                    "student_id": student.id,
                    "full_name": student.full_name,
                    "group_name": student.group_name,
                    "course_id": course_result["course_id"],
                    "course_name": course_result["course_name"],
                    "subject": course_result["subject"],
                    "attendance_rate": course_result["attendance_rate"],
                    "average_grade": course_result["average_grade"],
                    "final_score": course_result["final_score"],
                    "risk_status": course_result["risk_status"],
                }
            )
            continue

        report_rows.append(
            {
                "student_id": student.id,
                "full_name": student.full_name,
                "group_name": student.group_name,
                "course_id": selected_course.id if selected_course else None,
                "course_name": selected_course.name if selected_course else "All courses",
                "subject": "Combined",
                "attendance_rate": summary["attendance_rate"],
                "average_grade": summary["average_grade"],
                "final_score": summary["final_score"],
                "risk_status": summary["risk_status"],
            }
        )

    return report_rows
