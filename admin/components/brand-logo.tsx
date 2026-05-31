import { cn } from "@/lib/utils";

type BrandLogoProps = {
  compact?: boolean;
  className?: string;
};

export function BrandLogo({ compact = false, className }: BrandLogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <span className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-950 text-white shadow-sm">
        <svg viewBox="0 0 40 40" className="h-10 w-10" aria-hidden="true">
          <rect width="40" height="40" rx="8" fill="currentColor" className="text-slate-950" />
          <path d="M10 25.5h13.5c3 0 5.5-2.1 5.5-5s-2.5-5-5.5-5h-7c-1.7 0-3-1-3-2.4s1.3-2.6 3-2.6H30" fill="none" stroke="white" strokeWidth="3.2" strokeLinecap="round" />
          <path d="M10 30h20" stroke="#38bdf8" strokeWidth="3.2" strokeLinecap="round" />
        </svg>
      </span>
      {!compact && (
        <span className="leading-tight">
          <span className="block text-sm font-semibold text-slate-950 dark:text-slate-50">SHM Next</span>
          <span className="block text-xs text-muted-foreground">Billing platform</span>
        </span>
      )}
    </span>
  );
}
