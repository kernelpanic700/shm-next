"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

export const navItems = [
  { href: "/dashboard", label: "dashboard", mark: "DB" },
  { href: "/services", label: "services", mark: "SV" },
  { href: "/tariffs", label: "tariffs", mark: "TR" },
  { href: "/payments", label: "payments", mark: "PY" },
  { href: "/profile", label: "profile", mark: "PR" },
] as const;

export function BottomNav() {
  const pathname = usePathname();
  const { t } = useI18n();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-200 bg-white lg:hidden">
      <div className="grid h-16 grid-cols-5">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex h-full w-full flex-col items-center justify-center gap-1 text-xs font-medium",
              pathname === item.href ? "text-slate-950" : "text-slate-500"
            )}
          >
            <span
              className={cn(
                "flex h-6 w-8 items-center justify-center rounded border text-[10px] font-semibold",
                pathname === item.href ? "border-slate-950 bg-slate-950 text-white" : "border-slate-300"
              )}
            >
              {item.mark}
            </span>
            <span className="max-w-full truncate px-1">{t(item.label)}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
