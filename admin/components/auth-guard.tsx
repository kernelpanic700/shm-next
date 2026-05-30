'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, accessToken } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);

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
    // Check both zustand state AND localStorage
    if (!isAuthenticated && !accessToken && !hasTokenInStorage && !isLoginPage) {
      router.push('/login');
    }
  }, [isAuthenticated, accessToken, hasTokenInStorage, router, isLoginPage]);

  // Always render children - let client-side redirect handle auth
  // This prevents Next.js from showing 404 during SSR
  return <>{children}</>;
}