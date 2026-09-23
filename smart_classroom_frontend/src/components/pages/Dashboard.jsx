import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import api from "../../api/api";

export default function Dashboard() {
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [studentsRes, coursesRes, gradesRes] = await Promise.all([
          api.get("/students/"),
          api.get("/courses/"),
          api.get("/grades/"),
        ]);
        setStudents(studentsRes.data || []);
        setCourses(coursesRes.data || []);
        setGrades(gradesRes.data || []);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Загрузка данных...</div>
      </div>
    );
  }

  // Calculate basic statistics
  const totalStudents = students.length;
  const totalCourses = courses.length;
  const totalGrades = grades.length;
  const avgGrade = grades.length > 0 
    ? (grades.reduce((sum, g) => sum + g.score, 0) / grades.length).toFixed(1)
    : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Студентов</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalStudents}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Курсов</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalCourses}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Оценок</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalGrades}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Средний балл</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{avgGrade}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ваши оценки</CardTitle>
        </CardHeader>
        <CardContent>
          {grades.length === 0 ? (
            <p className="text-gray-500">Оценок пока нет</p>
          ) : (
            <div className="space-y-2">
              {grades.slice(0, 10).map((grade) => (
                <div key={grade.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <span className="font-medium">{grade.subject}</span>
                  <span className={`px-2 py-1 rounded ${
                    grade.score >= 80 ? 'bg-green-100 text-green-800' :
                    grade.score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {grade.score.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
