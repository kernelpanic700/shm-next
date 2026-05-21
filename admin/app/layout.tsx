'use client';

import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/components/query-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { AuthGuard } from "@/components/auth-guard";
import { SidebarNav } from "@/components/sidebar-nav";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/store/auth";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { logout, user } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <AuthGuard>
              <div className="flex h-screen flex-col">
                <header className="flex items-center justify-between border-b px-4 py-2">
                  <h1 className="text-lg font-semibold">SHM Next Admin</h1>
                  {user && (
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">{user.email}</span>
                      <Button variant="ghost" size="sm" onClick={handleLogout}>
                        <LogOut className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </header>
                <div className="flex flex-1 overflow-hidden">
                  <aside className="w-64 border-r bg-muted/40">
                    <SidebarNav />
                  </aside>
                  <main className="flex-1 overflow-auto">
                    {children}
                  </main>
                </div>
              </div>
            </AuthGuard>
          </QueryProvider>
        </ThemeProvider>
        <Toaster />
      </body>
    </html>
  );
}