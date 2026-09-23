import { useState, useEffect } from "react";
import { Calendar, Clock, MapPin, User } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import api from "../../api/api";

export default function Schedule() {
  const [lectures, setLectures] = useState([]);
  const [scheduleLoading, setScheduleLoading] = useState(true);
  const [showPastLectures, setShowPastLectures] = useState(false);
  const [weekOffset, setWeekOffset] = useState(0);

  useEffect(() => {
    const fetchLectures = async () => {
      try {
        const response = await api.get("/lectures/");
        setLectures(response.data || []);
      } catch {
        console.error("Error fetching lectures");
      } finally {
        setScheduleLoading(false);
      }
    };

    fetchLectures();
  }, []);

  if (scheduleLoading) {
    return <div className="text-gray-500">Загрузка расписания...</div>;
  }

  // Get current week start and end
  const today = new Date();
  const currentWeekStart = new Date(today);
  currentWeekStart.setDate(today.getDate() - today.getDay());
  const currentWeekEnd = new Date(currentWeekStart);
  currentWeekEnd.setDate(currentWeekStart.getDate() + 6);

  // Adjust for week offset
  const weekStart = new Date(currentWeekStart);
  weekStart.setDate(currentWeekStart.getDate() + (weekOffset * 7));
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);

  // Filter lectures for current week
  const filteredLectures = lectures.filter(lecture => {
    const lectureDate = new Date(lecture.date);
    const isThisWeek = lectureDate >= weekStart && lectureDate <= weekEnd;
    const isPast = lectureDate < currentWeekStart && lecture.status === "completed";
    
    if (!showPastLectures && isPast) return false;
    return isThisWeek;
  });

  // Group lectures by date
  const groupedLectures = filteredLectures.reduce((acc, lecture) => {
    const date = lecture.date;
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(lecture);
    return acc;
  }, {});

  const sortedDates = Object.keys(groupedLectures).sort();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Расписание лекций</CardTitle>
          <CardDescription>Ваши предстоящие лекции</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setWeekOffset(weekOffset - 1)}
              disabled={weekOffset <= -4}
            >
              ← Предыдущая неделя
            </Button>
            <span className="text-sm font-medium">
              {weekStart.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })} - {weekEnd.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setWeekOffset(weekOffset + 1)}
              disabled={weekOffset >= 4}
            >
              Следующая неделя →
            </Button>
            <div className="flex items-center gap-2 ml-auto">
              <input
                type="checkbox"
                id="showPast"
                checked={showPastLectures}
                onChange={(e) => setShowPastLectures(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="showPast" className="text-sm">Показать прошлые</label>
            </div>
          </div>

          {sortedDates.length === 0 ? (
            <p className="text-gray-500">Лекций на эту неделю нет</p>
          ) : (
            <div className="space-y-6">
              {sortedDates.map((date) => (
                <div key={date}>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    {new Date(date).toLocaleDateString('ru-RU', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </h3>
                  <div className="space-y-3">
                    {groupedLectures[date].map((lecture) => (
                      <div
                        key={lecture.id}
                        className="border rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900 mb-2">
                              {lecture.title}
                            </h4>
                            <div className="space-y-1 text-sm text-gray-600">
                              <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4" />
                                <span>{lecture.time} ({lecture.duration} мин)</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <MapPin className="h-4 w-4" />
                                <span>{lecture.room}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <User className="h-4 w-4" />
                                <span>{lecture.subject}</span>
                              </div>
                            </div>
                          </div>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-medium ${
                              lecture.status === "completed"
                                ? "bg-green-100 text-green-800"
                                : lecture.status === "scheduled"
                                  ? "bg-blue-100 text-blue-800"
                                  : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {lecture.status === "completed"
                              ? "Завершено"
                              : lecture.status === "scheduled"
                                ? "Запланировано"
                                : lecture.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
