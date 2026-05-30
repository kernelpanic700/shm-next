'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '@/lib/api';

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (phone: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (phone, password) => {
        try {
          const response = await api.post('/auth/login', { phone, password });
          // API returns { success, data: { access_token, refresh_token, ... } }
          // Extract token data from response
          const tokenData = response.data.data || response.data;
          const { access_token, refresh_token } = tokenData;

          // Store in localStorage FIRST for API interceptor
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          // Also set cookies for middleware
          document.cookie = `access_token=${access_token}; path=/; SameSite=Lax`;
          document.cookie = `refresh_token=${refresh_token}; path=/; SameSite=Lax`;

          // Update zustand state
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            user: { id: '', email: phone, name: '' },
            isAuthenticated: true,
          });
        } catch (error: any) {
          // Clear any partial auth state
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
);