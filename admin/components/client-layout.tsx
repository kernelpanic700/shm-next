'use client';

import { useAuthStore } from "@/lib/store/auth";
import { useRouter, usePathname } from "next/navigation";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarNav } from "@/components/sidebar-nav";
import { LanguageSwitcher } from "@/components/language-switcher";
import { useTranslation } from "react-i18next";

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const { logout, user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const isLoginPage = pathname === '/login';
  const { t } = useTranslation();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (isLoginPage) {
    return (
      <div className="flex h-screen flex-col">
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b px-4 py-2">
        <h1 className="text-lg font-semibold">SHM Next Admin</h1>
        {user && (
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <span className="text-sm text-muted-foreground">{user.email}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout} title={t('Logout')}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        )}
      </header>
      <div className="flex flex-1">
        <aside className="w-64 border-r bg-muted/40">
          <SidebarNav />
        </aside>
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
