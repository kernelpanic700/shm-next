import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1",
  timeout: 10000,
});

// Request interceptor: attach the access token.
api.interceptors.request.use(
  (config) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: unwrap ApiResponse.data and handle token refresh.
api.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === "object" && "data" in response.data) {
      response.data = response.data.data;
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
      if (refreshToken) {
        try {
          const response = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1"}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          const tokenData = response.data.data || response.data;
          localStorage.setItem("access_token", tokenData.access_token);
          originalRequest.headers.Authorization = `Bearer ${tokenData.access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Types
export interface Abonent {
  id: string;
  phone: string;
  email?: string;
  full_name: string;
  balance: number;
  status: string;
}

export interface Payment {
  id: string;
  amount: number;
  status: string;
  created_at: string;
  method?: string;
}

export interface Service {
  id: string;
  name: string;
  price: number;
  status: string;
  is_active: boolean;
}

export interface Tariff {
  id: string;
  name: string;
  price: number;
  speed: string;
  is_active: boolean;
}
