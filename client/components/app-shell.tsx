"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BottomNav, navItems } from "@/components/bottom-nav";
import { LanguageSwitcher } from "@/components/language-switcher";
import { useAuth } from "@/components/auth-provider";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { isClientRegistrationEnabled } from "@/lib/config";
import { BrandLogo } from "@/components/brand-logo";

const publicRoutes = new Set(
  isClientRegistrationEnabled ? ["/login", "/register"] : ["/login"]
);

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuth();
  const { t } = useI18n();
  const isPublicRoute = publicRoutes.has(pathname);

  if (isPublicRoute || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="fixed right-4 top-4 z-50">
          <LanguageSwitcher />
        </div>
        {children}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-16 items-center border-b border-slate-200 px-6">
          <Link href="/dashboard" className="flex items-center gap-3">
            <BrandLogo />
          </Link>
        </div>

        <nav className="space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors",
                  active
                    ? "bg-slate-950 text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                )}
              >
                <span className="flex h-6 w-6 items-center justify-center rounded border border-current text-[10px] font-semibold">
                  {item.mark}
                </span>
                {t(item.label)}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <Link href="/dashboard" className="flex items-center gap-3 lg:hidden">
              <BrandLogo compact />
              <span className="text-sm font-semibold">SHM Next</span>
            </Link>
            <div className="hidden lg:block">
              <p className="text-sm font-semibold">{t("personalAccount")}</p>
              <p className="text-xs text-slate-500">{t("secureWorkspace")}</p>
            </div>
            <div className="flex items-center gap-2">
              <LanguageSwitcher />
              <button
                type="button"
                onClick={logout}
                className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                {t("logout")}
              </button>
            </div>
          </div>
        </header>
        <main className="pb-20 lg:pb-0">{children}</main>
      </div>
      <BottomNav />
    </div>
  );
}
