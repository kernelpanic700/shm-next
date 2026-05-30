import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/components/query-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { AuthGuard } from "@/components/auth-guard";
import { ClientLayout } from "@/components/client-layout";
import { Toaster } from "@/components/ui/sonner";
import { LanguageProvider } from "@/lib/i18n/LanguageProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "SHM Next Admin",
  description: "Admin panel for SHM Next",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <LanguageProvider>
            <QueryProvider>
              <AuthGuard>
                <ClientLayout>{children}</ClientLayout>
              </AuthGuard>
            </QueryProvider>
          </LanguageProvider>
        </ThemeProvider>
        <Toaster />
      </body>
    </html>
  );
}
