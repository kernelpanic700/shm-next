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
        const response = await api.post('/auth/login', { phone, password });
        const { access_token, refresh_token } = response.data.data;
        
        set({
          accessToken: access_token,
          refreshToken: refresh_token,
          user: { id: '', email: phone, name: '' },
          isAuthenticated: true,
        });
      },
      
      logout: () => {
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