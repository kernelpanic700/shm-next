"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";

export function AuthWrapper({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const [isClient, setIsClient] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (loading || !isClient) return;

    const publicRoutes = ["/login", "/register", "/forgot-password"];

    if (!isAuthenticated && !publicRoutes.includes(pathname)) {
      router.replace("/login");
    }
  }, [isAuthenticated, loading, router, isClient, pathname]);

  if (loading || !isClient) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="h-10 w-10 rounded-md border-2 border-slate-300 border-t-slate-950" />
      </div>
    );
  }

  return children;
}
