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
  validateAdminSession: () => Promise<boolean>;
  setUser: (user: User | null) => void;
}

function clearStoredAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  document.cookie = 'access_token=; path=/; Max-Age=0; SameSite=Lax';
  document.cookie = 'refresh_token=; path=/; Max-Age=0; SameSite=Lax';
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
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

          const isAdmin = await get().validateAdminSession();
          if (!isAdmin) {
            throw new Error('Admin privileges required');
          }

          // Update zustand state
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            user: { id: '', email: phone, name: '' },
            isAuthenticated: true,
          });
        } catch (error: any) {
          // Clear any partial auth state
          clearStoredAuth();
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
        clearStoredAuth();
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      validateAdminSession: async () => {
        try {
          const response = await api.get('/auth/me');
          const profile = response.data.data || response.data;
          const isAdmin = profile?.role === 'admin';

          if (!isAdmin) {
            clearStoredAuth();
            set({
              user: null,
              accessToken: null,
              refreshToken: null,
              isAuthenticated: false,
            });
            return false;
          }

          set({
            user: {
              id: String(profile.id || ''),
              email: String(profile.phone || profile.email || ''),
              name: String(profile.full_name || 'Administrator'),
            },
            isAuthenticated: true,
          });
          return true;
        } catch {
          clearStoredAuth();
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
          });
          return false;
        }
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
