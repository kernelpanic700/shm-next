import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// API Types
export interface Abonent {
  id: string;
  name: string;
  full_name?: string;
  phone: string;
  account_number?: string;
  email?: string;
  address?: string;
  status: 'active' | 'inactive' | 'suspended' | 'ACTIVE' | 'INACTIVE' | 'BLOCKED' | 'SUSPENDED';
  balance: number;
  created_at: string;
  updated_at: string;
}

export interface Tariff {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  billing_cycle: 'monthly' | 'quarterly' | 'yearly';
  is_active: boolean;
  created_at: string;
}

export interface Service {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  is_active: boolean;
  created_at: string;
}

export interface Payment {
  id: string;
  abonent_id: string;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed';
  payment_method: string;
  created_at: string;
}

export interface SpoolTask {
  id: string;
  action_type: string;
  status: 'NEW' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'RETRY';
  priority: number;
  retry_count: number;
  max_retries: number;
  execute_after: string | null;
  created_at: string;
  updated_at: string;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_message: string | null;
}

export interface BillingCycle {
  id: string;
  period: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}