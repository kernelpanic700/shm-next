"use client";

import { useEffect, useState } from "react";
import { AuthProvider } from "./auth-provider";

export function AuthClientWrapper({ children }: { children: React.ReactNode }) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return <>{children}</>;
  }

  return <AuthProvider>{children}</AuthProvider>;
}