import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("doctor_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("doctor_token");
      localStorage.removeItem("doctor_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    const detail =
      error?.response?.data?.detail || error?.message || "Something went wrong. Please try again.";
    return Promise.reject(new Error(detail));
  }
);

export default api;
