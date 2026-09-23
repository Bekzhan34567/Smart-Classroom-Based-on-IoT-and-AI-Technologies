from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("/", response_model=schemas.CourseResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        if teacher is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher account is not linked to a teacher profile",
            )
        if course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can create courses only for themselves",
            )

    return crud.create_course(db, course)


@router.get("/", response_model=list[schemas.CourseResponse])
def read_courses(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_courses_for_user(db, user)


@router.get("/catalog", response_model=list[schemas.CourseResponse], dependencies=[Depends(get_current_user)])
def read_course_catalog(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_active_courses_for_user(db, user)


@router.put("/{course_id}", response_model=schemas.CourseResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def update_course(
    course_id: int,
    course: schemas.CourseUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        current_course = crud.get_course_by_id(db, course_id)
        if current_course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        if (
            teacher is None
            or current_course.teacher_id != teacher.id
            or course.teacher_id != teacher.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can update only their own courses",
            )
    return crud.update_course(db, course_id, course)


@router.post("/{course_id}/archive", response_model=schemas.CourseResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def archive_course(course_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        current_course = crud.get_course_by_id(db, course_id)
        if teacher is None or current_course is None or current_course.teacher_id != teacher.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers can archive only their own courses")
    return crud.archive_course(db, course_id)


@router.post("/{course_id}/regenerate-code", response_model=schemas.CourseResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def regenerate_course_code(course_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        current_course = crud.get_course_by_id(db, course_id)
        if teacher is None or current_course is None or current_course.teacher_id != teacher.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers can regenerate codes only for their own courses")
    return crud.regenerate_course_join_code(db, course_id)


@router.delete("/{course_id}", dependencies=[Depends(require_role("admin", "teacher"))])
def delete_course(course_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        current_course = crud.get_course_by_id(db, course_id)
        if teacher is None or current_course is None or current_course.teacher_id != teacher.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers can delete only their own courses")
    crud.delete_course(db, course_id)
    return {"message": "Course deleted successfully"}
