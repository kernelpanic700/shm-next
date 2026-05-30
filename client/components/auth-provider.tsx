"use client";

import { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/api";

interface AuthContextType {
  isAuthenticated: boolean;
  login: (phone: string, password: string) => Promise<void>;
  logout: () => void;
  user: any;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<{ phone: string } | null>(null);
  const [loading, setLoading] = useState(true);

  const login = async (phone: string, password: string) => {
    try {
      const response = await api.post("/auth/login", { phone, password });
      // API returns { success, data: { access_token, refresh_token, ... } }
      // The api interceptor extracts response.data.data, so response.data is already the token data
      const { access_token, refresh_token } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      localStorage.setItem("user_phone", phone);
      setIsAuthenticated(true);
      setUser({ phone });
    } catch (error) {
      console.error("Auth: login error", error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_phone");
    setIsAuthenticated(false);
    setUser(null);
  };

  // Check token on mount
  useEffect(() => {
    const checkToken = () => {
      try {
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem("access_token");
          const userPhone = localStorage.getItem("user_phone");
          const hasToken = !!token;
          setIsAuthenticated(hasToken);
          setUser(hasToken && userPhone ? { phone: userPhone } : null);
        }
      } catch (error) {
        console.error("AuthProvider: error checking token:", error);
      } finally {
        setLoading(false);
      }
    };

    // Small delay to ensure client-side execution
    const timer = setTimeout(checkToken, 50);
    return () => clearTimeout(timer);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, user, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
