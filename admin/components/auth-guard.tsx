'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, accessToken, logout, validateAdminSession } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const checkedTokenRef = useRef<string | null>(null);

  // Don't redirect on the login page itself
  const isLoginPage = pathname === '/login';

  // Also check localStorage directly for tokens (handles async persist)
  const hasTokenInStorage = typeof window !== 'undefined' &&
    (localStorage.getItem('access_token') || localStorage.getItem('refresh_token'));

  // Ensure we're on the client before checking auth state
  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (isLoginPage || !isClient) {
      return;
    }

    // Check both zustand state AND localStorage
    if (!isAuthenticated && !accessToken && !hasTokenInStorage) {
      router.push('/login');
      return;
    }

    const token = typeof hasTokenInStorage === 'string' ? hasTokenInStorage : accessToken;
    if (token && checkedTokenRef.current !== token && !isChecking) {
      checkedTokenRef.current = token;
      setIsChecking(true);
      validateAdminSession().then((isAdmin) => {
        if (!isAdmin) {
          checkedTokenRef.current = null;
          logout();
          router.push('/login');
        }
      }).finally(() => setIsChecking(false));
    }
  }, [isAuthenticated, accessToken, hasTokenInStorage, router, isLoginPage, isClient, isChecking, logout, validateAdminSession]);

  // Always render children - let client-side redirect handle auth
  // This prevents Next.js from showing 404 during SSR
  return <>{children}</>;
}
