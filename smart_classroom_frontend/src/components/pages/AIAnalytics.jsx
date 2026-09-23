import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import api from "../../api/api";

export default function AIAnalytics() {
  const [loading, setLoading] = useState(true);
  const [mlAvailable, setMlAvailable] = useState(false);

  useEffect(() => {
    const checkML = async () => {
      try {
        const response = await api.get("/ml-analytics/predictions");
        if (response.data) {
          setMlAvailable(true);
        }
      } catch {
        setMlAvailable(false);
      } finally {
        setLoading(false);
      }
    };

    checkML();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Аналитика</CardTitle>
          <CardDescription>Машинное обучение и предсказания</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-gray-500">Загрузка...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Demo data when ML is not available
  const demoData = {
    overview: {
      total_students: 30,
      students_at_risk: 5,
      risk_percentage: 16.7,
      average_predicted_grade: 78.5,
    },
    predictions: [
      {
        student_id: 1,
        full_name: "Иванов Иван",
        current_grade: 85,
        predicted_grade: 88,
        predicted_risk: false,
        confidence: 0.85,
      },
      {
        student_id: 2,
        full_name: "Петров Петр",
        current_grade: 72,
        predicted_grade: 75,
        predicted_risk: false,
        confidence: 0.78,
      },
      {
        student_id: 3,
        full_name: "Сидоров Сидор",
        current_grade: 58,
        predicted_grade: 62,
        predicted_risk: true,
        confidence: 0.72,
      },
      {
        student_id: 4,
        full_name: "Козлова Анна",
        current_grade: 91,
        predicted_grade: 93,
        predicted_risk: false,
        confidence: 0.9,
      },
      {
        student_id: 5,
        full_name: "Морозов Дмитрий",
        current_grade: 65,
        predicted_grade: 68,
        predicted_risk: true,
        confidence: 0.68,
      },
    ],
    anomalies: [
      {
        student_id: 3,
        full_name: "Сидоров Сидор",
        type: "attendance",
        value: 45,
      },
      {
        student_id: 5,
        full_name: "Морозов Дмитрий",
        type: "grades",
        value: 52,
      },
    ],
    course_recommendations: {
      Математика: ["Увеличить практические занятия", "Добавить онлайн-тесты"],
      Физика: [
        "Использовать интерактивные демонстрации",
        "Дополнительные материалы",
      ],
      Программирование: ["Больше проектов", "Парное программирование"],
    },
  };

  const data = mlAvailable
    ? {
        overview: {},
        predictions: [],
        anomalies: [],
        course_recommendations: {},
      }
    : demoData;

  return (
    <div className="space-y-6">
      {!mlAvailable && (
        <Card className="bg-amber-50 border-amber-200">
          <CardHeader>
            <CardTitle className="text-amber-900">Демо режим</CardTitle>
            <CardDescription className="text-amber-700">
              ML функционал отключен (требует scikit-learn). Показаны
              демо-данные.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Обзор AI аналитики</CardTitle>
          <CardDescription>
            Статистика и метрики машинного обучения
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg border">
              <p className="text-sm text-gray-600">Всего студентов</p>
              <p className="text-2xl font-bold text-blue-900">
                {data.overview.total_students || 0}
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-red-50 to-orange-50 rounded-lg border">
              <p className="text-sm text-gray-600">Студенты риска</p>
              <p className="text-2xl font-bold text-red-900">
                {data.overview.students_at_risk || 0}
              </p>
              <p className="text-xs text-red-600">
                {data.overview.risk_percentage?.toFixed(1) || 0}%
              </p>
            </div>
            <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border">
              <p className="text-sm text-gray-600">Средняя оценка (ML)</p>
              <p className="text-2xl font-bold text-green-900">
                {Math.round(data.overview.average_predicted_grade || 0)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Предсказания успеваемости</CardTitle>
          <CardDescription>ML прогнозы для студентов</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Студент
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Текущая
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Прогноз
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Риск
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">
                    Уверенность
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.predictions.slice(0, 10).map((prediction) => (
                  <tr
                    key={prediction.student_id}
                    className="border-b hover:bg-gray-50"
                  >
                    <td className="py-3 px-4">{prediction.full_name}</td>
                    <td className="py-3 px-4">
                      {Math.round(prediction.current_grade)}%
                    </td>
                    <td className="py-3 px-4">
                      {Math.round(prediction.predicted_grade)}%
                    </td>
                    <td className="py-3 px-4">
                      {prediction.predicted_risk ? (
                        <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs">
                          Да
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                          Нет
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {Math.round(prediction.confidence * 100)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Обнаруженные аномалии</CardTitle>
          <CardDescription>Детекция нестандартного поведения</CardDescription>
        </CardHeader>
        <CardContent>
          {data.anomalies.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              Аномалий не обнаружено
            </p>
          ) : (
            <div className="space-y-3">
              {data.anomalies.map((anomaly) => (
                <div
                  key={anomaly.student_id}
                  className="p-4 border rounded-lg bg-amber-50"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">
                        {anomaly.full_name}
                      </p>
                      <p className="text-sm text-gray-600">
                        Тип:{" "}
                        {anomaly.type === "attendance"
                          ? "Посещаемость"
                          : "Оценки"}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-amber-900">
                        {Math.round(anomaly.value)}%
                      </p>
                      <p className="text-xs text-amber-600">Значение</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Рекомендации по курсам</CardTitle>
          <CardDescription>
            AI предложения для улучшения обучения
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(data.course_recommendations).map(
              ([course, recommendations]) => (
                <div key={course} className="p-4 border rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">{course}</h4>
                  {recommendations.length > 0 ? (
                    <ul className="space-y-1">
                      {recommendations.map((rec, index) => (
                        <li
                          key={index}
                          className="text-sm text-gray-600 flex items-start gap-2"
                        >
                          <span className="text-blue-500 mt-1">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-500">Нет рекомендаций</p>
                  )}
                </div>
              ),
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
