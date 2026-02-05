import axios from "axios";
import { clearToken, getToken, isTokenExpired, notifyAuthExpired } from "./session";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api"
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (!token) {
    return config;
  }

  if (isTokenExpired(token)) {
    clearToken();
    notifyAuthExpired("expired");
    return config;
  }

  config.headers = config.headers ?? {};
  (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const requestUrl = String(error.config?.url || "");
    const isLoginRequest = requestUrl.includes("/auth/login");

    if (status === 401 && !isLoginRequest) {
      clearToken();
      notifyAuthExpired("unauthorized");
    }

    return Promise.reject(error);
  }
);

export default api;
