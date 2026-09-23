from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("/", response_model=schemas.EnrollmentResponse, dependencies=[Depends(require_role("admin"))])
def create_enrollment(enrollment: schemas.EnrollmentCreate, db: Session = Depends(get_db)):
    return crud.create_enrollment(db, enrollment)


@router.post("/self", response_model=schemas.EnrollmentResponse, dependencies=[Depends(require_role("student"))])
def self_enroll(
    payload: schemas.SelfEnrollmentRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud.enroll_current_student(db, user, payload.course_id, payload.join_code)


@router.get("/", response_model=list[schemas.EnrollmentResponse])
def read_enrollments(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_enrollments_for_user(db, user)
