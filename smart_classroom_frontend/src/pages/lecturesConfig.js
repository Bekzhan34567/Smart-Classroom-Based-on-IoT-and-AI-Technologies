export const initialLectureForm = {
  title: "",
  subject: "",
  date: "",
  recurring_until: "",
  time: "",
  teacher_id: "",
  course_id: "",
  status: "scheduled",
};

export const initialCourseForm = {
  name: "",
  group_name: "",
  teacher_id: "",
  status: "active",
};

export const initialStudentEnrollmentForm = {
  course_id: "",
  join_code: "",
};

export const initialEnrollmentForm = {
  student_id: "",
  course_id: "",
};

export const initialAttendanceForm = {
  student_id: "",
  lecture_id: "",
  status: "present",
};

export const initialGradeForm = {
  student_id: "",
  course_id: "",
  subject: "",
  score: "",
};

export const initialSummaryForm = {
  student_id: "",
};

export const initialReportForm = {
  group_name: "",
  course_id: "",
};

export const initialLoginForm = {
  email: "",
  password: "",
};

export const initialRegisterForm = {
  full_name: "",
  email: "",
  password: "",
  role: "student",
  group_name: "",
};

export const initialPasswordResetForm = {
  user_id: "",
  new_password: "Temp12345!",
};

export const initialChangePasswordForm = {
  current_password: "",
  new_password: "",
};

export const initialStaffForm = {
  full_name: "",
  email: "",
  password: "",
  role: "teacher",
  group_name: "",
  subject: "",
};

export const initialGroupForm = {
  name: "",
};

export const initialProfileForm = {
  full_name: "",
  email: "",
  group_name: "",
  subject: "",
};

export function getAvailableTabs(role) {
  if (!role) return ["auth"];
  if (role === "admin") return ["overview", "accounts", "courses", "lectures", "results", "analytics"];
  if (role === "teacher") return ["overview", "courses", "lectures", "results", "analytics"];
  return ["overview", "courses", "schedule", "achievements"];
}
