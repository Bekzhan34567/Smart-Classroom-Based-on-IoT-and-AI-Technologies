import { useState, useEffect } from "react";
import { Plus, Edit, Trash2, X, Shield, User as UserIcon } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import api from "../../api/api";

export default function UsersManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "teacher",
    subject: "",
    group_name: ""
  });

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await api.get("/auth/users");
        setUsers(response.data);
      } catch {
        console.error("Error fetching users");
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const handleCreate = () => {
    setEditingUser(null);
    setFormData({
      full_name: "",
      email: "",
      password: "",
      role: "teacher",
      subject: "",
      group_name: ""
    });
    setShowModal(true);
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      full_name: user.full_name,
      email: user.email,
      password: "",
      role: user.role,
      subject: user.subject || "",
      group_name: user.group_name || ""
    });
    setShowModal(true);
  };

  const handleDelete = async (userId) => {
    if (!confirm("Вы уверены, что хотите удалить этого пользователя?")) return;
    
    try {
      await api.delete(`/auth/users/${userId}`);
      setUsers(users.filter(u => u.id !== userId));
    } catch {
      alert("Ошибка при удалении пользователя");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingUser) {
        // Update user
        const response = await api.put(`/auth/users/${editingUser.id}`, {
          full_name: formData.full_name,
          email: formData.email,
          role: formData.role,
          subject: formData.role === "teacher" ? formData.subject : null,
          group_name: formData.role === "student" ? formData.group_name : null
        });
        setUsers(users.map(u => u.id === editingUser.id ? response.data : u));
      } else {
        // Create new user via register-staff
        const response = await api.post("/auth/register-staff", {
          full_name: formData.full_name,
          email: formData.email,
          password: formData.password,
          role: formData.role,
          subject: formData.role === "teacher" ? formData.subject : null
        });
        setUsers([...users, response.data]);
      }
      setShowModal(false);
    } catch {
      alert("Ошибка при сохранении пользователя");
    }
  };

  if (loading) {
    return <div className="text-gray-500">Загрузка пользователей...</div>;
  }

  const roleColors = {
    admin: "bg-purple-100 text-purple-800",
    teacher: "bg-blue-100 text-blue-800",
    student: "bg-green-100 text-green-800"
  };

  const roleNames = {
    admin: "Администратор",
    teacher: "Преподаватель",
    student: "Студент"
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Управление пользователями</h2>
          <p className="text-gray-600">Всего пользователей: {users.length}</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Добавить пользователя
        </Button>
      </div>
      
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Пользователь</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Email</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Роль</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Дополнительно</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-700">Действия</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <UserIcon className="h-4 w-4 text-gray-400" />
                        <span className="font-medium">{user.full_name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-600">{user.email}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${roleColors[user.role]}`}>
                        {roleNames[user.role]}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">
                      {user.role === "teacher" && user.subject && <span>{user.subject}</span>}
                      {user.role === "student" && user.group_name && <span>{user.group_name}</span>}
                      {user.role === "admin" && <Shield className="h-4 w-4 text-purple-500" />}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex gap-2 justify-end">
                        <Button variant="outline" size="sm" onClick={() => handleEdit(user)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700" onClick={() => handleDelete(user.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>{editingUser ? "Редактировать пользователя" : "Добавить пользователя"}</CardTitle>
              <Button variant="ghost" size="icon" className="absolute right-4 top-4" onClick={() => setShowModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium">ФИО</label>
                  <input
                    type="text"
                    className="w-full mt-1 p-2 border rounded"
                    value={formData.full_name}
                    onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Email</label>
                  <input
                    type="email"
                    className="w-full mt-1 p-2 border rounded"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>
                {!editingUser && (
                  <div>
                    <label className="text-sm font-medium">Пароль</label>
                    <input
                      type="password"
                      className="w-full mt-1 p-2 border rounded"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      required
                    />
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium">Роль</label>
                  <select
                    className="w-full mt-1 p-2 border rounded"
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    required
                  >
                    <option value="teacher">Преподаватель</option>
                    <option value="student">Студент</option>
                    <option value="admin">Администратор</option>
                  </select>
                </div>
                {formData.role === "teacher" && (
                  <div>
                    <label className="text-sm font-medium">Предмет</label>
                    <input
                      type="text"
                      className="w-full mt-1 p-2 border rounded"
                      value={formData.subject}
                      onChange={(e) => setFormData({...formData, subject: e.target.value})}
                    />
                  </div>
                )}
                {formData.role === "student" && (
                  <div>
                    <label className="text-sm font-medium">Группа</label>
                    <input
                      type="text"
                      className="w-full mt-1 p-2 border rounded"
                      value={formData.group_name}
                      onChange={(e) => setFormData({...formData, group_name: e.target.value})}
                    />
                  </div>
                )}
                <div className="flex gap-2 pt-4">
                  <Button type="submit" className="flex-1">
                    {editingUser ? "Сохранить" : "Создать"}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
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
