# Smart Classroom Frontend

React + Vite dashboard for the Smart Classroom diploma prototype.

## Features

- authentication panel
- student and teacher management
- course and enrollment flow
- lecture scheduling
- attendance and grade entry
- analytics and student summary

## Run

From the frontend folder:

```bash
npm install
npm run dev
```

Frontend URL:

- `http://127.0.0.1:5173`

## Backend Connection

The frontend uses:

- `http://127.0.0.1:8000`

Make sure the FastAPI backend is running before opening the dashboard.

## Demo Flow

1. Register an `admin`
2. Login
3. Create a teacher
4. Create a course
5. Create a student
6. Enroll the student
7. Create a lecture
8. Add attendance
9. Add a grade
10. Load the student summary
