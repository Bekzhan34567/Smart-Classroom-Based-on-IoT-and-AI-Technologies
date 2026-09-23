import { useState, useEffect } from "react";
import { Plus, Edit, Trash2, X } from "lucide-react";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import api from "../../api/api";

export default function CoursesManagement() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    group_name: "",
    teacher_id: null,
    status: "active",
  });
  const [groups, setGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [coursesRes, userRes, groupsRes, teachersRes] = await Promise.all(
          [
            api.get("/courses/"),
            api.get("/auth/me"),
            api.get("/groups/"),
            api.get("/teachers/"),
          ],
        );
        setCourses(coursesRes.data);
        setUser(userRes.data);
        setGroups(groupsRes.data);
        setTeachers(teachersRes.data);
      } catch {
        console.error("Error fetching data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const isTeacherOrAdmin =
    user && (user.role === "teacher" || user.role === "admin");

  const handleCreate = () => {
    setEditingCourse(null);
    setFormData({
      name: "",
      group_name: "",
      teacher_id: user.role === "teacher" ? user.teacher_id : null,
      status: "active",
    });
    setShowModal(true);
  };

  const handleEdit = (course) => {
    setEditingCourse(course);
    setFormData({
      name: course.name,
      group_name: course.group_name,
      teacher_id: course.teacher_id,
      status: course.status,
    });
    setShowModal(true);
  };

  const handleDelete = async (courseId) => {
    if (!confirm("Вы уверены, что хотите удалить этот курс?")) return;

    try {
      await api.delete(`/courses/${courseId}`);
      setCourses(courses.filter((c) => c.id !== courseId));
    } catch {
      alert("Ошибка при удалении курса");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingCourse) {
        const response = await api.put(
          `/courses/${editingCourse.id}`,
          formData,
        );
        setCourses(
          courses.map((c) => (c.id === editingCourse.id ? response.data : c)),
        );
      } else {
        const response = await api.post("/courses/", formData);
        setCourses([...courses, response.data]);
      }
      setShowModal(false);
    } catch {
      alert("Ошибка при сохранении курса");
    }
  };

  if (loading) {
    return <div className="text-gray-500">Загрузка курсов...</div>;
  }

  return (
    <div className="space-y-6">
      {isTeacherOrAdmin && (
        <div className="flex justify-end">
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Создать курс
          </Button>
        </div>
      )}

      {courses.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-gray-500">Курсы пока не созданы</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {courses.map((course) => (
            <Card key={course.id}>
              <CardHeader>
                <CardTitle className="text-lg">{course.name}</CardTitle>
                <CardDescription>{course.group_name}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        course.status === "active"
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {course.status === "active" ? "Активен" : "Архив"}
                    </span>
                  </div>
                  {isTeacherOrAdmin && (
                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleEdit(course)}
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        Редактировать
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:text-red-700"
                        onClick={() => handleDelete(course.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>
                {editingCourse ? "Редактировать курс" : "Создать курс"}
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-4 top-4"
                onClick={() => setShowModal(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Название курса</label>
                  <input
                    type="text"
                    className="w-full mt-1 p-2 border rounded"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Группа</label>
                  <select
                    className="w-full mt-1 p-2 border rounded"
                    value={formData.group_name}
                    onChange={(e) =>
                      setFormData({ ...formData, group_name: e.target.value })
                    }
                    required
                  >
                    <option value="">Выберите группу</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.name}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </div>
                {user.role === "admin" && (
                  <div>
                    <label className="text-sm font-medium">Преподаватель</label>
                    <select
                      className="w-full mt-1 p-2 border rounded"
                      value={formData.teacher_id || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          teacher_id: e.target.value
                            ? parseInt(e.target.value)
                            : null,
                        })
                      }
                      required
                    >
                      <option value="">Выберите преподавателя</option>
                      {teachers.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.full_name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="flex gap-2 pt-4">
                  <Button type="submit" className="flex-1">
                    {editingCourse ? "Сохранить" : "Создать"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowModal(false)}
                  >
                    Отмена
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
