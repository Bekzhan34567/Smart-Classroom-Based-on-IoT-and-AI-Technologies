from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/", response_model=list[schemas.StudentResponse])
def read_students(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_students_for_user(db, user)


@router.get("/{student_id}", response_model=schemas.StudentResponse)
def read_student(student_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    student = crud.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    if user.role.lower() == "student":
        if user.student_profile is None or user.student_profile.id != student_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    return student
