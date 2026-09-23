from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .auth_utils import hash_password
from .course_codes import generate_join_code

VALID_ATTENDANCE_STATUSES = {"present", "absent", "late"}
WORKDAY_START = time(8, 0)
WORKDAY_END = time(18, 0)
DEFAULT_LECTURE_DURATION = 80


def _get_lecture_by_id(db: Session, lecture_id: int):
    return db.query(models.Lecture).filter(models.Lecture.id == lecture_id).first()


def _get_teacher_by_email(db: Session, email: str):
    return db.query(models.Teacher).filter(models.Teacher.email == email).first()


def _get_student_by_email(db: Session, email: str):
    return db.query(models.Student).filter(models.Student.email == email).first()


def _get_group_by_name(db: Session, name: str):
    return db.query(models.Group).filter(models.Group.name == name).first()


def _normalize_join_code(join_code: str):
    return join_code.strip().upper()


def _generate_unique_join_code(db: Session):
    while True:
        join_code = generate_join_code()
        exists = db.query(models.Course).filter(models.Course.join_code == join_code).first()
        if exists is None:
            return join_code


def get_teacher_for_user(db: Session, user: models.User):
    return user.teacher_profile or _get_teacher_by_email(db, user.email)


def _get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_student_for_user(db: Session, user: models.User):
    return user.student_profile or _get_student_by_email(db, user.email)


def _get_course_ids_for_student(db: Session, student_id: int):
    rows = (
        db.query(models.Enrollment.course_id)
        .filter(models.Enrollment.student_id == student_id)
        .all()
    )
    return [course_id for (course_id,) in rows]


def _get_course_ids_for_teacher(db: Session, teacher_id: int):
    rows = (
        db.query(models.Course.id)
        .filter(models.Course.teacher_id == teacher_id)
        .all()
    )
    return [course_id for (course_id,) in rows]


def _is_student_enrolled_in_course(db: Session, student_id: int, course_id: int):
    return (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.student_id == student_id,
            models.Enrollment.course_id == course_id,
        )
        .first()
        is not None
    )


def _normalize_attendance_status(status_value: str):
    normalized_status = status_value.strip().lower()
    if normalized_status not in VALID_ATTENDANCE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attendance status must be one of: {', '.join(sorted(VALID_ATTENDANCE_STATUSES))}",
        )
    return normalized_status


def _assert_schedule_rules(lecture: schemas.LectureCreate):
    if lecture.date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture date cannot be in the past",
        )

    if lecture.date.weekday() >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lectures can only be scheduled on working days",
        )

    duration = lecture.duration or DEFAULT_LECTURE_DURATION
    if duration <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture duration must be positive",
        )

    start_dt = datetime.combine(lecture.date, lecture.time)
    end_dt = start_dt + timedelta(minutes=duration)

    if lecture.time < WORKDAY_START or end_dt.time() > WORKDAY_END:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lectures must be scheduled within working hours (08:00-18:00)",
        )


def _assert_teacher_schedule_conflict(
    db: Session,
    lecture: schemas.LectureCreate,
    exclude_lecture_id: int | None = None,
):
    duration = lecture.duration or DEFAULT_LECTURE_DURATION
    new_start = datetime.combine(lecture.date, lecture.time)
    new_end = new_start + timedelta(minutes=duration)

    teacher_lectures = (
        db.query(models.Lecture)
        .filter(
            models.Lecture.teacher_id == lecture.teacher_id,
            models.Lecture.date == lecture.date,
        )
        .all()
    )

    for existing in teacher_lectures:
        if exclude_lecture_id is not None and existing.id == exclude_lecture_id:
            continue
        existing_duration = existing.duration or DEFAULT_LECTURE_DURATION
        existing_start = datetime.combine(existing.date, existing.time)
        existing_end = existing_start + timedelta(minutes=existing_duration)

        if new_start < existing_end and existing_start < new_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher already has a lecture scheduled at this time",
            )


def _lecture_payload_to_model(lecture: schemas.LectureCreate):
    payload = lecture.model_dump()
    payload["duration"] = payload["duration"] or DEFAULT_LECTURE_DURATION
    return models.Lecture(**payload)


def create_student(db: Session, student: schemas.StudentCreate):
    group = _get_group_by_name(db, student.group_name.strip())
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected group does not exist",
        )
    existing_user = _get_user_by_email(db, student.email)
    payload = student.model_dump()

    if existing_user is not None:
        if existing_user.role.lower() != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already used by a non-student account",
            )
        payload["user_id"] = existing_user.id

    db_student = models.Student(**payload)
    db.add(db_student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this email already exists",
        ) from exc
    db.refresh(db_student)
    return db_student


def get_students(db: Session):
    return db.query(models.Student).order_by(models.Student.id.desc()).all()


def get_students_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role == "admin":
        return get_students(db)
    if role == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            return []
        course_ids = _get_course_ids_for_teacher(db, teacher.id)
        if not course_ids:
            return []
        return (
            db.query(models.Student)
            .join(models.Enrollment, models.Enrollment.student_id == models.Student.id)
            .filter(models.Enrollment.course_id.in_(course_ids))
            .distinct()
            .order_by(models.Student.full_name.asc())
            .all()
        )
    if role == "student":
        student = get_student_for_user(db, user)
        return [student] if student is not None else []
    return []


def get_student_by_id(db: Session, student_id: int):
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def create_group(db: Session, group: schemas.GroupCreate):
    normalized_name = group.name.strip()
    if not normalized_name:
        raise HTTPException(status_code=400, detail="Group name is required")

    db_group = models.Group(name=normalized_name)
    db.add(db_group)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group with this name already exists",
        ) from exc
    db.refresh(db_group)
    return db_group


def get_groups(db: Session):
    return db.query(models.Group).order_by(models.Group.name.asc()).all()


def create_teacher(db: Session, teacher: schemas.TeacherCreate):
    existing_user = _get_user_by_email(db, teacher.email)
    payload = teacher.model_dump()

    if existing_user is not None:
        if existing_user.role.lower() != "teacher":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already used by a non-teacher account",
            )
        payload["user_id"] = existing_user.id

    db_teacher = models.Teacher(**payload)
    db.add(db_teacher)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher with this email already exists",
        ) from exc
    db.refresh(db_teacher)
    return db_teacher


def get_teachers(db: Session):
    return db.query(models.Teacher).order_by(models.Teacher.id.desc()).all()


def get_teachers_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role == "admin":
        return get_teachers(db)
    if role == "teacher":
        teacher = get_teacher_for_user(db, user)
        return [teacher] if teacher is not None else []
    if role == "student":
        student = get_student_for_user(db, user)
        if student is None:
            return []
        course_ids = _get_course_ids_for_student(db, student.id)
        if not course_ids:
            return []
        return (
            db.query(models.Teacher)
            .join(models.Course, models.Course.teacher_id == models.Teacher.id)
            .filter(models.Course.id.in_(course_ids))
            .distinct()
            .order_by(models.Teacher.full_name.asc())
            .all()
        )
    return []


def get_teacher_by_id(db: Session, teacher_id: int):
    return db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()


def create_course(db: Session, course: schemas.CourseCreate):
    teacher = get_teacher_by_id(db, course.teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    if course.group_name:
        group = _get_group_by_name(db, course.group_name.strip())
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")

    payload = course.model_dump()
    payload["group_name"] = course.group_name.strip() if course.group_name else None
    payload["status"] = course.status or "active"
    payload["join_code"] = _generate_unique_join_code(db)
    db_course = models.Course(**payload)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def get_courses(db: Session):
    return db.query(models.Course).order_by(models.Course.id.desc()).all()


def get_active_courses(db: Session):
    return (
        db.query(models.Course)
        .filter(models.Course.status != "archived")
        .order_by(models.Course.id.desc())
        .all()
    )


def get_active_courses_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role != "student":
        return get_active_courses(db)

    student = get_student_for_user(db, user)
    if student is None:
        return []

    return (
        db.query(models.Course)
        .filter(
            models.Course.status != "archived",
            (models.Course.group_name.is_(None))
            | (models.Course.group_name == student.group_name),
        )
        .order_by(models.Course.id.desc())
        .all()
    )


def get_courses_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role == "admin":
        return get_courses(db)
    if role == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            return []
        return (
            db.query(models.Course)
            .filter(models.Course.teacher_id == teacher.id)
            .order_by(models.Course.id.desc())
            .all()
        )
    if role == "student":
        student = get_student_for_user(db, user)
        if student is None:
            return []
        course_ids = _get_course_ids_for_student(db, student.id)
        if not course_ids:
            return []
        return (
            db.query(models.Course)
            .filter(models.Course.id.in_(course_ids))
            .order_by(models.Course.id.desc())
            .all()
        )
    return []


def get_course_by_id(db: Session, course_id: int):
    return db.query(models.Course).filter(models.Course.id == course_id).first()


def get_course_by_join_code(db: Session, join_code: str):
    normalized_code = _normalize_join_code(join_code)
    return db.query(models.Course).filter(models.Course.join_code == normalized_code).first()


def update_course(db: Session, course_id: int, course: schemas.CourseUpdate):
    db_course = get_course_by_id(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    teacher = get_teacher_by_id(db, course.teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    if course.group_name:
        group = _get_group_by_name(db, course.group_name.strip())
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")

    db_course.name = course.name
    db_course.group_name = course.group_name.strip() if course.group_name else None
    db_course.teacher_id = course.teacher_id
    if course.status:
        db_course.status = course.status
    db.commit()
    db.refresh(db_course)
    return db_course


def archive_course(db: Session, course_id: int):
    db_course = get_course_by_id(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    db_course.status = "archived"
    db.commit()
    db.refresh(db_course)
    return db_course


def regenerate_course_join_code(db: Session, course_id: int):
    db_course = get_course_by_id(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    db_course.join_code = _generate_unique_join_code(db)
    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: int):
    db_course = get_course_by_id(db, course_id)
    if db_course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(db_course)
    db.commit()


def create_enrollment(db: Session, enrollment: schemas.EnrollmentCreate):
    student = get_student_by_id(db, enrollment.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    course = get_course_by_id(db, enrollment.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.status == "archived":
        raise HTTPException(status_code=400, detail="Archived courses cannot accept new enrollments")
    if course.group_name and course.group_name != student.group_name:
        raise HTTPException(
            status_code=400,
            detail="This course is assigned to a different group",
        )

    db_enrollment = models.Enrollment(**enrollment.model_dump())
    db.add(db_enrollment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled in this course",
        ) from exc
    db.refresh(db_enrollment)
    return db_enrollment


def get_enrollments(db: Session):
    return db.query(models.Enrollment).order_by(models.Enrollment.id.desc()).all()


def enroll_current_student(db: Session, user: models.User, course_id: int | None = None, join_code: str | None = None):
    student = get_student_for_user(db, user)
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")

    resolved_course_id = course_id
    if join_code:
        course = get_course_by_join_code(db, join_code)
        if course is None:
            raise HTTPException(status_code=404, detail="Course with this join code was not found")
        resolved_course_id = course.id

    if resolved_course_id is None:
        raise HTTPException(status_code=400, detail="Course ID or join code is required")

    return create_enrollment(
        db,
        schemas.EnrollmentCreate(student_id=student.id, course_id=resolved_course_id),
    )


def get_enrollments_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role == "admin":
        return get_enrollments(db)
    if role == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            return []
        course_ids = _get_course_ids_for_teacher(db, teacher.id)
        if not course_ids:
            return []
        return (
            db.query(models.Enrollment)
            .filter(models.Enrollment.course_id.in_(course_ids))
            .order_by(models.Enrollment.id.desc())
            .all()
        )
    if role == "student":
        student = get_student_for_user(db, user)
        if student is None:
            return []
        return (
            db.query(models.Enrollment)
            .filter(models.Enrollment.student_id == student.id)
            .order_by(models.Enrollment.id.desc())
            .all()
        )
    return []


def create_lecture(db: Session, lecture: schemas.LectureCreate):
    teacher = get_teacher_by_id(db, lecture.teacher_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    if lecture.course_id is not None:
        course = get_course_by_id(db, lecture.course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        if course.teacher_id != lecture.teacher_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course teacher does not match lecture teacher",
            )

    _assert_schedule_rules(lecture)
    _assert_teacher_schedule_conflict(db, lecture)

    db_lecture = _lecture_payload_to_model(lecture)
    db.add(db_lecture)
    db.commit()
    db.refresh(db_lecture)
    return db_lecture


def create_lecture_series(db: Session, lecture: schemas.LectureSeriesCreate):
    if lecture.recurring_until < lecture.date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester end date must be after the first lecture date",
        )

    teacher = get_teacher_by_id(db, lecture.teacher_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    if lecture.course_id is not None:
        course = get_course_by_id(db, lecture.course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        if course.teacher_id != lecture.teacher_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course teacher does not match lecture teacher",
            )

    generated_lectures: list[schemas.LectureCreate] = []
    current_date = lecture.date
    while current_date <= lecture.recurring_until:
        lecture_item = schemas.LectureCreate(
            title=lecture.title,
            subject=lecture.subject,
            date=current_date,
            time=lecture.time,
            teacher_id=lecture.teacher_id,
            course_id=lecture.course_id,
            duration=lecture.duration,
            room=lecture.room,
            status=lecture.status,
        )
        _assert_schedule_rules(lecture_item)
        _assert_teacher_schedule_conflict(db, lecture_item)
        generated_lectures.append(lecture_item)
        current_date += timedelta(days=7)

    created_lectures = []
    for lecture_item in generated_lectures:
        db_lecture = _lecture_payload_to_model(lecture_item)
        db.add(db_lecture)
        created_lectures.append(db_lecture)

    db.commit()
    for db_lecture in created_lectures:
        db.refresh(db_lecture)

    return created_lectures


def update_lecture(db: Session, lecture_id: int, lecture: schemas.LectureUpdate):
    db_lecture = _get_lecture_by_id(db, lecture_id)
    if db_lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")

    teacher = get_teacher_by_id(db, lecture.teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if lecture.course_id is not None:
        course = get_course_by_id(db, lecture.course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")
        if course.teacher_id != lecture.teacher_id:
            raise HTTPException(status_code=400, detail="Course teacher does not match lecture teacher")

    lecture_payload = schemas.LectureCreate(**lecture.model_dump())
    _assert_schedule_rules(lecture_payload)
    _assert_teacher_schedule_conflict(db, lecture_payload, exclude_lecture_id=lecture_id)

    db_lecture.title = lecture.title
    db_lecture.subject = lecture.subject
    db_lecture.date = lecture.date
    db_lecture.time = lecture.time
    db_lecture.teacher_id = lecture.teacher_id
    db_lecture.course_id = lecture.course_id
    db_lecture.duration = lecture.duration or DEFAULT_LECTURE_DURATION
    db_lecture.room = lecture.room
    db_lecture.status = lecture.status
    db.commit()
    db.refresh(db_lecture)
    return db_lecture


def archive_lecture(db: Session, lecture_id: int):
    db_lecture = _get_lecture_by_id(db, lecture_id)
    if db_lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")
    db_lecture.status = "archived"
    db.commit()
    db.refresh(db_lecture)
    return db_lecture


def delete_lecture(db: Session, lecture_id: int):
    db_lecture = _get_lecture_by_id(db, lecture_id)
    if db_lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")
    db.delete(db_lecture)
    db.commit()


def get_lectures(db: Session):
    return db.query(models.Lecture).order_by(models.Lecture.date.desc(), models.Lecture.time.desc()).all()


def get_lectures_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role == "admin":
        return get_lectures(db)
    if role == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            return []
        return (
            db.query(models.Lecture)
            .filter(models.Lecture.teacher_id == teacher.id)
            .order_by(models.Lecture.date.desc(), models.Lecture.time.desc())
            .all()
        )
    if role == "student":
        student = get_student_for_user(db, user)
        if student is None:
            return []
        course_ids = _get_course_ids_for_student(db, student.id)
        if not course_ids:
            return []
        return (
            db.query(models.Lecture)
            .filter(models.Lecture.course_id.in_(course_ids))
            .order_by(models.Lecture.date.desc(), models.Lecture.time.desc())
            .all()
        )
    return []


def get_schedule_for_user(db: Session, user: models.User):
    role = user.role.lower()

    if role == "admin":
        lectures = get_lectures(db)
    elif role == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            return []
        lectures = (
            db.query(models.Lecture)
            .filter(models.Lecture.teacher_id == teacher.id)
            .order_by(models.Lecture.date.asc(), models.Lecture.time.asc())
            .all()
        )
    elif role == "student":
        student = user.student_profile or _get_student_by_email(db, user.email)
        if student is None:
            return []
        course_ids = (
            db.query(models.Enrollment.course_id)
            .filter(models.Enrollment.student_id == student.id)
            .all()
        )
        flattened_ids = [course_id for (course_id,) in course_ids]
        if not flattened_ids:
            return []
        lectures = (
            db.query(models.Lecture)
            .filter(models.Lecture.course_id.in_(flattened_ids))
            .order_by(models.Lecture.date.asc(), models.Lecture.time.asc())
            .all()
        )
    else:
        return []

    return [
        schemas.ScheduleItemResponse(
            lecture_id=lecture.id,
            title=lecture.title,
            subject=lecture.subject,
            date=lecture.date,
            time=lecture.time,
            duration=lecture.duration,
            room=lecture.room,
            teacher_id=lecture.teacher_id,
            course_id=lecture.course_id,
            status=lecture.status,
        )
        for lecture in lectures
    ]


def create_attendance(db: Session, attendance: schemas.AttendanceCreate):
    student = get_student_by_id(db, attendance.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    lecture = _get_lecture_by_id(db, attendance.lecture_id)
    if lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")

    status_value = _normalize_attendance_status(attendance.status)
    db_attendance = models.Attendance(
        student_id=attendance.student_id,
        lecture_id=attendance.lecture_id,
        status=status_value,
    )
    db.add(db_attendance)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance for this student and lecture already exists",
        ) from exc
    db.refresh(db_attendance)
    return db_attendance


def get_attendance(db: Session):
    return db.query(models.Attendance).order_by(models.Attendance.timestamp.desc()).all()


def get_attendance_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role == "admin":
        return get_attendance(db)
    if role == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            return []
        lecture_ids = (
            db.query(models.Lecture.id)
            .filter(models.Lecture.teacher_id == teacher.id)
            .all()
        )
        flattened_ids = [lecture_id for (lecture_id,) in lecture_ids]
        if not flattened_ids:
            return []
        return (
            db.query(models.Attendance)
            .filter(models.Attendance.lecture_id.in_(flattened_ids))
            .order_by(models.Attendance.timestamp.desc())
            .all()
        )
    if role == "student":
        student = get_student_for_user(db, user)
        if student is None:
            return []
        return (
            db.query(models.Attendance)
            .filter(models.Attendance.student_id == student.id)
            .order_by(models.Attendance.timestamp.desc())
            .all()
        )
    return []


def mark_attendance(db: Session, student_id: int, lecture_id: int, status_value: str):
    student = get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    lecture = _get_lecture_by_id(db, lecture_id)
    if lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")
    if lecture.course_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture is not linked to a course",
        )
    if not _is_student_enrolled_in_course(db, student_id, lecture.course_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not enrolled in this lecture course",
        )

    normalized_status = _normalize_attendance_status(status_value)
    record = db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id,
        models.Attendance.lecture_id == lecture_id,
    ).first()

    if record is None:
        record = models.Attendance(
            student_id=student_id,
            lecture_id=lecture_id,
            status=normalized_status,
        )
        db.add(record)
    else:
        record.status = normalized_status

    db.commit()
    db.refresh(record)
    return record


def mark_attendance_for_user(
    db: Session,
    user: models.User,
    student_id: int,
    lecture_id: int,
    status_value: str,
):
    if user.role.lower() == "teacher":
        teacher = get_teacher_for_user(db, user)
        lecture = _get_lecture_by_id(db, lecture_id)
        if teacher is None or lecture is None or lecture.teacher_id != teacher.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    return mark_attendance(db, student_id, lecture_id, status_value)


def mark_lecture_attendance(
    db: Session,
    lecture_id: int,
    records: list[schemas.AttendanceBulkRecord] | None = None,
    status_value: str = "present",
):
    lecture = _get_lecture_by_id(db, lecture_id)
    if lecture is None:
        raise HTTPException(status_code=404, detail="Lecture not found")

    if lecture.course_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture is not linked to a course",
        )

    enrollments = db.query(models.Enrollment).filter(models.Enrollment.course_id == lecture.course_id).all()
    if not enrollments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No enrolled students found for this lecture",
        )

    results = []
    normalized_status = _normalize_attendance_status(status_value)
    enrolled_student_ids = {enrollment.student_id for enrollment in enrollments}
    requested_records = records or [
        schemas.AttendanceBulkRecord(
            student_id=enrollment.student_id,
            status=normalized_status,
        )
        for enrollment in enrollments
    ]

    requested_student_ids = {record.student_id for record in requested_records}
    if requested_student_ids != enrolled_student_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance records must include exactly the enrolled students for this lecture course",
        )

    for attendance_record in requested_records:
        normalized_record_status = _normalize_attendance_status(attendance_record.status)
        record = db.query(models.Attendance).filter(
            models.Attendance.student_id == attendance_record.student_id,
            models.Attendance.lecture_id == lecture_id,
        ).first()

        if record is None:
            record = models.Attendance(
                student_id=attendance_record.student_id,
                lecture_id=lecture_id,
                status=normalized_record_status,
            )
            db.add(record)
        else:
            record.status = normalized_record_status

        results.append(record)

    db.commit()
    for record in results:
        db.refresh(record)
    return results


def mark_lecture_attendance_for_user(
    db: Session,
    user: models.User,
    lecture_id: int,
    records: list[schemas.AttendanceBulkRecord],
):
    if user.role.lower() == "teacher":
        teacher = get_teacher_for_user(db, user)
        lecture = _get_lecture_by_id(db, lecture_id)
        if teacher is None or lecture is None or lecture.teacher_id != teacher.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    return mark_lecture_attendance(db, lecture_id, records=records)


def create_grade(db: Session, grade: schemas.GradeCreate):
    _validate_grade_assignment(db, grade.student_id, grade.course_id)

    db_grade = models.Grade(**grade.model_dump())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade


def get_grade_by_id(db: Session, grade_id: int):
    return db.query(models.Grade).filter(models.Grade.id == grade_id).first()


def get_grades(db: Session):
    return db.query(models.Grade).order_by(models.Grade.id.desc()).all()


def _validate_grade_assignment(db: Session, student_id: int, course_id: int):
    student = get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    course = get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollment = (
        db.query(models.Enrollment)
        .filter(
            models.Enrollment.student_id == student_id,
            models.Enrollment.course_id == course_id,
        )
        .first()
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not enrolled in the selected course",
        )
    return course


def _assert_teacher_can_manage_grade(
    db: Session,
    teacher: models.Teacher,
    grade: schemas.GradeCreate | schemas.GradeUpdate,
):
    course = _validate_grade_assignment(db, grade.student_id, grade.course_id)
    if course.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers can manage grades only for their own courses",
        )
    if grade.subject.strip().lower() != teacher.subject.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers can add grades only for their own subject",
        )


def create_grade_for_user(db: Session, user: models.User, grade: schemas.GradeCreate):
    if user.role.lower() == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            raise HTTPException(status_code=403, detail="Forbidden")
        _assert_teacher_can_manage_grade(db, teacher, grade)
    return create_grade(db, grade)


def update_grade(db: Session, grade_id: int, grade: schemas.GradeUpdate):
    db_grade = get_grade_by_id(db, grade_id)
    if db_grade is None:
        raise HTTPException(status_code=404, detail="Grade not found")

    _validate_grade_assignment(db, grade.student_id, grade.course_id)

    db_grade.student_id = grade.student_id
    db_grade.course_id = grade.course_id
    db_grade.subject = grade.subject
    db_grade.score = grade.score
    db.commit()
    db.refresh(db_grade)
    return db_grade


def update_grade_for_user(db: Session, user: models.User, grade_id: int, grade: schemas.GradeUpdate):
    if user.role.lower() == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            raise HTTPException(status_code=403, detail="Forbidden")
        existing_grade = get_grade_by_id(db, grade_id)
        if existing_grade is None:
            raise HTTPException(status_code=404, detail="Grade not found")
        if existing_grade.course_id is not None:
            existing_course = get_course_by_id(db, existing_grade.course_id)
            owns_existing_grade = existing_course is not None and existing_course.teacher_id == teacher.id
        else:
            owns_existing_grade = existing_grade.subject.strip().lower() == teacher.subject.strip().lower()
        if not owns_existing_grade:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can edit only grades from their own courses",
            )
        _assert_teacher_can_manage_grade(db, teacher, grade)
    return update_grade(db, grade_id, grade)


def get_grades_for_user(db: Session, user: models.User):
    role = user.role.lower()
    if role == "admin":
        return get_grades(db)
    if role == "teacher":
        teacher = get_teacher_for_user(db, user)
        if teacher is None:
            return []
        course_ids = _get_course_ids_for_teacher(db, teacher.id)
        if not course_ids:
            return []
        student_ids = (
            db.query(models.Enrollment.student_id)
            .filter(models.Enrollment.course_id.in_(course_ids))
            .all()
        )
        flattened_student_ids = [student_id for (student_id,) in student_ids]
        if not flattened_student_ids:
            return []
        return (
            db.query(models.Grade)
            .filter(
                models.Grade.student_id.in_(flattened_student_ids),
                or_(
                    models.Grade.course_id.in_(course_ids),
                    and_(
                        models.Grade.course_id.is_(None),
                        models.Grade.subject == teacher.subject,
                    ),
                ),
            )
            .order_by(models.Grade.id.desc())
            .all()
        )
    if role == "student":
        student = get_student_for_user(db, user)
        if student is None:
            return []
        return (
            db.query(models.Grade)
            .filter(models.Grade.student_id == student.id)
            .order_by(models.Grade.id.desc())
            .all()
        )
    return []


def create_user(db: Session, user: schemas.UserCreate):
    role = user.role.lower()
    teacher = None
    student = None

    if role == "student":
        if not user.group_name or not user.group_name.strip():
            raise HTTPException(status_code=400, detail="Group is required for student accounts")
        if _get_group_by_name(db, user.group_name.strip()) is None:
            raise HTTPException(status_code=400, detail="Selected group does not exist")
    if role == "teacher" and (not user.subject or not user.subject.strip()):
        raise HTTPException(status_code=400, detail="Subject is required for teacher accounts")

    if role == "teacher":
        if user.teacher_id is not None:
            teacher = get_teacher_by_id(db, user.teacher_id)
            if teacher is None:
                raise HTTPException(status_code=404, detail="Teacher profile not found")
            if teacher.user_id is not None:
                raise HTTPException(status_code=400, detail="Teacher profile is already linked to a user")
    elif role == "student":
        if user.student_id is not None:
            student = get_student_by_id(db, user.student_id)
            if student is None:
                raise HTTPException(status_code=404, detail="Student profile not found")
            if student.user_id is not None:
                raise HTTPException(status_code=400, detail="Student profile is already linked to a user")

    db_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password),
        role=role,
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        ) from exc

    db.refresh(db_user)

    if role == "teacher":
        teacher = teacher or _get_teacher_by_email(db, db_user.email)
        if teacher is None:
            teacher = models.Teacher(
                full_name=db_user.full_name,
                subject=(user.subject or "General Subject").strip(),
                email=db_user.email,
                user_id=db_user.id,
            )
            db.add(teacher)
        elif teacher.user_id is None:
            teacher.user_id = db_user.id
    elif role == "student":
        student = student or _get_student_by_email(db, db_user.email)
        if student is None:
            student = models.Student(
                full_name=db_user.full_name,
                group_name=(user.group_name or "Self-registered").strip(),
                email=db_user.email,
                user_id=db_user.id,
            )
            db.add(student)
        elif student.user_id is None:
            student.user_id = db_user.id

    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session):
    return db.query(models.User).order_by(models.User.id.desc()).all()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def reset_user_password(db: Session, user_id: int, new_password: str):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role.lower() == "admin":
        admin_count = db.query(models.User).filter(models.User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin account")

    if user.teacher_profile is not None:
        user.teacher_profile.user_id = None
    if user.student_profile is not None:
        user.student_profile.user_id = None

    db.delete(user)
    db.commit()


def update_user_account(
    db: Session,
    target_user: models.User,
    payload: schemas.UserUpdateRequest,
):
    full_name = payload.full_name.strip()
    email = str(payload.email).strip().lower()

    if not full_name:
        raise HTTPException(status_code=400, detail="Full name is required")

    existing_user = _get_user_by_email(db, email)
    if existing_user is not None and existing_user.id != target_user.id:
        raise HTTPException(status_code=400, detail="Email already registered")

    target_user.full_name = full_name
    target_user.email = email

    role = target_user.role.lower()
    if role == "teacher":
        teacher = get_teacher_for_user(db, target_user)
        if teacher is None:
            raise HTTPException(status_code=404, detail="Teacher profile not found")
        if not payload.subject or not payload.subject.strip():
            raise HTTPException(status_code=400, detail="Subject is required for teacher accounts")
        teacher.full_name = full_name
        teacher.email = email
        teacher.subject = payload.subject.strip()
    elif role == "student":
        student = get_student_for_user(db, target_user)
        if student is None:
            raise HTTPException(status_code=404, detail="Student profile not found")
        if not payload.group_name or not payload.group_name.strip():
            raise HTTPException(status_code=400, detail="Group is required for student accounts")
        if _get_group_by_name(db, payload.group_name.strip()) is None:
            raise HTTPException(status_code=400, detail="Selected group does not exist")
        student.full_name = full_name
        student.email = email
        student.group_name = payload.group_name.strip()

    db.commit()
    db.refresh(target_user)
    return target_user
