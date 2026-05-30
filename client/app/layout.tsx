import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { AuthWrapper } from "@/components/auth-wrapper";
import { QueryProvider } from "@/components/query-provider";
import { LanguageProvider } from "@/lib/i18n";
import { AppShell } from "@/components/app-shell";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "SHM Next",
  description: "Subscriber self-service portal",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className={inter.className}>
        <QueryProvider>
          <LanguageProvider>
            <AuthProvider>
              <AuthWrapper>
                <AppShell>{children}</AppShell>
              </AuthWrapper>
            </AuthProvider>
          </LanguageProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
