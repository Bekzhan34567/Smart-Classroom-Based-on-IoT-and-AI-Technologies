from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/lectures", tags=["Lectures"])


@router.post("/", response_model=schemas.LectureResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def create_lecture(
    lecture: schemas.LectureCreate,
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
        if lecture.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can create lectures only for themselves",
            )

    return crud.create_lecture(db, lecture)


@router.post("/series", response_model=list[schemas.LectureResponse], dependencies=[Depends(require_role("admin", "teacher"))])
def create_lecture_series(
    lecture: schemas.LectureSeriesCreate,
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
        if lecture.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can create lectures only for themselves",
            )

    return crud.create_lecture_series(db, lecture)


@router.get("/", response_model=list[schemas.LectureResponse])
def read_lectures(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_lectures_for_user(db, user)


@router.get("/my-schedule", response_model=list[schemas.ScheduleItemResponse])
def my_schedule(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_schedule_for_user(db, user)


@router.put("/{lecture_id}", response_model=schemas.LectureResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def update_lecture(
    lecture_id: int,
    lecture: schemas.LectureUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        current_lecture = crud._get_lecture_by_id(db, lecture_id)
        if current_lecture is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
        if (
            teacher is None
            or current_lecture.teacher_id != teacher.id
            or lecture.teacher_id != teacher.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can update only their own lectures",
            )
    return crud.update_lecture(db, lecture_id, lecture)


@router.post("/{lecture_id}/archive", response_model=schemas.LectureResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def archive_lecture(lecture_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        current_lecture = crud._get_lecture_by_id(db, lecture_id)
        if teacher is None or current_lecture is None or current_lecture.teacher_id != teacher.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers can archive only their own lectures")
    return crud.archive_lecture(db, lecture_id)


@router.delete("/{lecture_id}", dependencies=[Depends(require_role("admin", "teacher"))])
def delete_lecture(lecture_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role.lower() == "teacher":
        teacher = crud.get_teacher_for_user(db, user)
        current_lecture = crud._get_lecture_by_id(db, lecture_id)
        if teacher is None or current_lecture is None or current_lecture.teacher_id != teacher.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers can delete only their own lectures")
    crud.delete_lecture(db, lecture_id)
    return {"message": "Lecture deleted successfully"}
