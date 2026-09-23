import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 8000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("smart_classroom_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("smart_classroom_token");
      window.dispatchEvent(new CustomEvent("smart-classroom-unauthorized"));
    }
    return Promise.reject(error);
  },
);

export default api;
