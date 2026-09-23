from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..dependencies import require_role

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/", response_model=schemas.GroupResponse, dependencies=[Depends(require_role("admin"))])
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    return crud.create_group(db, group)


@router.get("/", response_model=list[schemas.GroupResponse])
def read_groups(db: Session = Depends(get_db)):
    return crud.get_groups(db)
