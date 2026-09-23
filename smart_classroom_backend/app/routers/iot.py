from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, models, schemas

router = APIRouter(prefix="/iot", tags=["IoT Simulation"])


@router.post("/attendance-event")
def simulate_iot_attendance(event: schemas.IoTAttendanceEvent, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == event.student_id).first()
    lecture = db.query(models.Lecture).filter(models.Lecture.id == event.lecture_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    mapped_status = "present" if event.sensor_status == "detected" else "absent"
    attendance_record = crud.mark_attendance(
        db,
        event.student_id,
        event.lecture_id,
        mapped_status,
    )

    return {
        "message": "IoT attendance event processed successfully",
        "student_id": event.student_id,
        "lecture_id": event.lecture_id,
        "sensor_status": event.sensor_status,
        "recorded_status": mapped_status
    }
