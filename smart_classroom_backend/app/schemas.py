from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):
    full_name: str
    group_name: str
    email: EmailStr
    user_id: int | None = None


class StudentResponse(StudentCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TeacherCreate(BaseModel):
    full_name: str
    subject: str
    email: EmailStr
    user_id: int | None = None


class TeacherResponse(TeacherCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class GroupCreate(BaseModel):
    name: str


class GroupResponse(GroupCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CourseCreate(BaseModel):
    name: str
    group_name: str | None = None
    teacher_id: int
    status: str = "active"


class CourseResponse(CourseCreate):
    id: int
    status: str
    join_code: str

    model_config = ConfigDict(from_attributes=True)


class CourseUpdate(BaseModel):
    name: str
    group_name: str | None = None
    teacher_id: int
    status: str | None = None


class SelfEnrollmentRequest(BaseModel):
    course_id: int | None = None
    join_code: str | None = None


class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int


class EnrollmentResponse(EnrollmentCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LectureCreate(BaseModel):
    title: str
    subject: str
    date: date
    time: time
    teacher_id: int
    course_id: int | None = None
    duration: int | None = 80
    room: str | None = None
    status: str = "scheduled"


class LectureSeriesCreate(BaseModel):
    title: str
    subject: str
    date: date
    recurring_until: date
    time: time
    teacher_id: int
    course_id: int | None = None
    duration: int | None = 80
    room: str | None = None
    status: str = "scheduled"


class LectureResponse(LectureCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LectureUpdate(BaseModel):
    title: str
    subject: str
    date: date
    time: time
    teacher_id: int
    course_id: int | None = None
    duration: int | None = 80
    room: str | None = None
    status: str = "scheduled"


class AttendanceCreate(BaseModel):
    student_id: int
    lecture_id: int
    status: str


class AttendanceMarkRequest(BaseModel):
    student_id: int
    lecture_id: int
    status: str


class AttendanceBulkRecord(BaseModel):
    student_id: int
    status: str


class AttendanceBulkMarkRequest(BaseModel):
    lecture_id: int
    records: list[AttendanceBulkRecord]


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    lecture_id: int
    status: str
    timestamp: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class GradeCreate(BaseModel):
    student_id: int
    course_id: int
    subject: str = Field(min_length=1)
    score: float = Field(ge=0, le=100)


class GradeUpdate(BaseModel):
    student_id: int
    course_id: int
    subject: str = Field(min_length=1)
    score: float = Field(ge=0, le=100)


class GradeResponse(BaseModel):
    id: int
    student_id: int
    # Old records may not have a course until they are edited.
    course_id: int | None = None
    subject: str
    score: float

    model_config = ConfigDict(from_attributes=True)


class IoTAttendanceEvent(BaseModel):
    student_id: int
    lecture_id: int
    sensor_status: str


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    role: str = Field(pattern="^(student|teacher|admin)$")
    group_name: str | None = None
    subject: str | None = None
    teacher_id: int | None = None
    student_id: int | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    teacher_id: int | None = None
    student_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPasswordResetRequest(BaseModel):
    new_password: str


class UserAdminResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    full_name: str
    email: EmailStr
    group_name: str | None = None
    subject: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ScheduleItemResponse(BaseModel):
    lecture_id: int
    title: str
    subject: str
    date: date
    time: time
    duration: int | None = None
    room: str | None = None
    teacher_id: int
    course_id: int | None = None
    status: str
