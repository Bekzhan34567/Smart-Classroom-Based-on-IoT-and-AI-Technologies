import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import api from "../../api/api";

export default function StudentsManagement() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const response = await api.get("/students/");
        setStudents(response.data);
      } catch {
        console.error("Error fetching students");
      } finally {
        setLoading(false);
      }
    };

    fetchStudents();
  }, []);

  if (loading) {
    return <div className="text-gray-500">Загрузка студентов...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Управление студентами</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {students.map((student) => (
            <div key={student.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <div>
                <p className="font-medium">{student.full_name}</p>
                <p className="text-sm text-gray-500">{student.email}</p>
              </div>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                {student.group_name}
              </span>
            </div>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-4 text-center">
          Показано {students.length} студентов
        </p>
      </CardContent>
    </Card>
  );
}
