'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated && !accessToken) {
      router.push('/login');
    }
  }, [isAuthenticated, accessToken, router]);

  if (!isAuthenticated && !accessToken) {
    return null;
  }

  return <>{children}</>;
}