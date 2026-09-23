# Smart Classroom Backend

FastAPI backend for the Smart Classroom diploma prototype.

## Modules

- `auth` for registration, login, and role-based access
- `students` and `teachers` for academic profiles
- `courses` and `enrollments` for academic structure
- `lectures` for lesson scheduling
- `attendance` and `grades` for learning records
- `analytics` for at-risk students and per-student summaries
- `iot` for attendance simulation

## Run

From the project root:

```bash
cp .env.example .env
source ../venv/bin/activate
uvicorn app.main:app --reload
```

If you start from `/Users/qwerty/Visual Studio projects`, then:

```bash
cd smart_classroom_backend
cp .env.example .env
source ../venv/bin/activate
uvicorn app.main:app --reload
```

Backend URL:

- `http://127.0.0.1:8000`
- docs: `http://127.0.0.1:8000/docs`

## First Admin

```bash
python3 scripts/bootstrap_admin.py
```

Bootstrap credentials:

- `admin@smartclassroom.edu`
- `Admin12345!`

## Demo Flow

1. Bootstrap the first `admin` account locally
2. Login as that admin
3. Create a teacher
4. Create a course
5. Create a student
6. Enroll the student into the course
7. Create a lecture for that course
8. Mark attendance
9. Add a grade
10. Open analytics in the frontend and load the student summary

## Notes

- SQLite is stored in `smart_classroom.db`
- CORS is enabled for local frontend development
- Some write operations require `admin` or `teacher` roles
- Public self-registration is limited to students; `teacher` and `admin` users should be created by an existing admin
- JWT access tokens are issued to every authenticated user, while permissions are enforced by role in the API
