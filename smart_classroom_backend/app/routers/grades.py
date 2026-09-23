from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.post("/", response_model=schemas.GradeResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def create_grade(grade: schemas.GradeCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.create_grade_for_user(db, user, grade)


@router.put("/{grade_id}", response_model=schemas.GradeResponse, dependencies=[Depends(require_role("admin", "teacher"))])
def update_grade(
    grade_id: int,
    grade: schemas.GradeUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud.update_grade_for_user(db, user, grade_id, grade)


@router.get(
    "/",
    response_model=list[schemas.GradeResponse],
    dependencies=[Depends(get_current_user)],
)
def read_grades(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_grades_for_user(db, user)
