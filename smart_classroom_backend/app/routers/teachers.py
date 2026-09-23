from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.get("/", response_model=list[schemas.TeacherResponse])
def read_teachers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_teachers_for_user(db, user)
