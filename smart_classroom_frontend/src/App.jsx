import { useState, useEffect } from "react";
import {
  GraduationCap,
  Users,
  BookOpen,
  Calendar,
  BarChart3,
  Brain,
  Settings,
  LogOut,
  UserCog,
} from "lucide-react";
import { Button } from "./components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import AuthPanels from "./pages/AuthPanels";
import { Toast } from "./components/ui/toast";
import api from "./api/api";
import Dashboard from "./components/pages/Dashboard";
import Schedule from "./components/pages/Schedule";
import CoursesManagement from "./components/pages/CoursesManagement";
import GradesManagement from "./components/pages/GradesManagement";
import StudentsManagement from "./components/pages/StudentsManagement";
import AIAnalytics from "./components/pages/AIAnalytics";
import Reports from "./components/pages/Reports";
import UsersManagement from "./components/pages/UsersManagement";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [toast, setToast] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("smart_classroom_token");
      if (token) {
        try {
          const response = await api.get("/auth/me");
          setUser(response.data);
        } catch {
          localStorage.removeItem("smart_classroom_token");
        }
      }
      setLoading(false);
    };

    checkAuth();

    const handleUnauthorized = () => {
      setUser(null);
      localStorage.removeItem("smart_classroom_token");
    };

    window.addEventListener("smart-classroom-unauthorized", handleUnauthorized);
    return () =>
      window.removeEventListener(
        "smart-classroom-unauthorized",
        handleUnauthorized,
      );
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setToast({ message: "Добро пожаловать!", type: "success" });
  };

  const handleLogout = () => {
    localStorage.removeItem("smart_classroom_token");
    setUser(null);
    setToast({ message: "Вы вышли из системы", type: "info" });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 flex items-center justify-center">
        <div className="text-gray-500">Загрузка...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <AuthPanels onLogin={handleLogin} />
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg">
                <GraduationCap className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Smart Classroom
                </h1>
                <p className="text-sm text-gray-600">
                  AI-Powered Learning Platform
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">
                  {user.full_name}
                </p>
                <p className="text-xs text-gray-500 capitalize">
                  {user.role === "student"
                    ? "Студент"
                    : user.role === "teacher"
                      ? "Преподаватель"
                      : "Администратор"}
                </p>
              </div>
              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
              </Button>
              <Button variant="outline" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Выйти
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b bg-white/60 backdrop-blur-sm">
        <div className="container mx-auto px-4">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList
              className={`grid w-full h-auto p-1 bg-transparent ${
                user.role === "student"
                  ? "grid-cols-4"
                  : user.role === "teacher"
                    ? "grid-cols-5"
                    : "grid-cols-7"
              }`}
            >
              <TabsTrigger
                value="dashboard"
                className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Дашборд
              </TabsTrigger>
              <TabsTrigger
                value="schedule"
                className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <Calendar className="h-4 w-4 mr-2" />
                Расписание
              </TabsTrigger>
              <TabsTrigger
                value="courses"
                className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <BookOpen className="h-4 w-4 mr-2" />
                Курсы
              </TabsTrigger>
              <TabsTrigger
                value="grades"
                className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
              >
                <Users className="h-4 w-4 mr-2" />
                {user.role === "student" ? "Оценки" : "Студенты"}
              </TabsTrigger>
              {user.role !== "student" && (
                <TabsTrigger
                  value="analytics"
                  className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
                >
                  <Brain className="h-4 w-4 mr-2" />
                  AI Аналитика
                </TabsTrigger>
              )}
              {user.role === "admin" && (
                <TabsTrigger
                  value="reports"
                  className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
                >
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Отчеты
                </TabsTrigger>
              )}
              {user.role === "admin" && (
                <TabsTrigger
                  value="users"
                  className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
                >
                  <UserCog className="h-4 w-4 mr-2" />
                  Пользователи
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="dashboard" className="mt-6">
              <Dashboard />
            </TabsContent>
            <TabsContent value="schedule" className="mt-6">
              <Schedule />
            </TabsContent>
            <TabsContent value="courses" className="mt-6">
              <CoursesManagement />
            </TabsContent>
            <TabsContent value="grades" className="mt-6">
              {user.role === "student" ? (
                <GradesManagement />
              ) : (
                <StudentsManagement />
              )}
            </TabsContent>
            {user.role !== "student" && (
              <TabsContent value="analytics" className="mt-6">
                <AIAnalytics />
              </TabsContent>
            )}
            {user.role === "admin" && (
              <TabsContent value="reports" className="mt-6">
                <Reports />
              </TabsContent>
            )}
            {user.role === "admin" && (
              <TabsContent value="users" className="mt-6">
                <UsersManagement />
              </TabsContent>
            )}
          </Tabs>
        </div>
      </nav>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default App;
