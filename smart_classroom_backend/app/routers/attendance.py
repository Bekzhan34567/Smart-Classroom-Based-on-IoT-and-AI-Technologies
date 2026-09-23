from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.get(
    "/",
    response_model=list[schemas.AttendanceResponse],
    dependencies=[Depends(get_current_user)],
)
def read_attendance(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_attendance_for_user(db, user)


@router.post("/mark", response_model=schemas.AttendanceResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def mark_attendance(
    payload: schemas.AttendanceMarkRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud.mark_attendance_for_user(
        db,
        user,
        payload.student_id,
        payload.lecture_id,
        payload.status,
    )


@router.post("/bulk", response_model=list[schemas.AttendanceResponse], dependencies=[Depends(require_role("admin", "teacher"))])
def mark_bulk_attendance(
    payload: schemas.AttendanceBulkMarkRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud.mark_lecture_attendance_for_user(
        db,
        user,
        payload.lecture_id,
        payload.records,
    )
