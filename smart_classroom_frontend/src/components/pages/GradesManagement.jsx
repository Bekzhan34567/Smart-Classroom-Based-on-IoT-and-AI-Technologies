import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import api from "../../api/api";

export default function GradesManagement() {
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGrades = async () => {
      try {
        const response = await api.get("/grades/");
        setGrades(response.data);
      } catch {
        console.error("Error fetching grades");
      } finally {
        setLoading(false);
      }
    };

    fetchGrades();
  }, []);

  if (loading) {
    return <div className="text-gray-500">Загрузка оценок...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ваши оценки</CardTitle>
      </CardHeader>
      <CardContent>
        {grades.length === 0 ? (
          <p className="text-gray-500">Оценок пока нет</p>
        ) : (
          <div className="space-y-2">
            {grades.map((grade) => (
              <div key={grade.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <div>
                  <p className="font-medium">{grade.subject}</p>
                  <p className="text-sm text-gray-500">{new Date(grade.date).toLocaleDateString('ru-RU')}</p>
                </div>
                <span className={`px-3 py-1 rounded font-bold ${
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
  );
}
