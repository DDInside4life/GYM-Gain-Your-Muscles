import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { AuthProvider } from "@/components/providers/auth-provider";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";

export const metadata: Metadata = {
  title: "GYM — Gain Your Muscles",
  description:
    "Умные тренировки и питание под твой уровень, цели и экипировку. Прогрессия каждую неделю.",
};

const themeBootstrap = `
(function(){try{var t=localStorage.getItem('gym.theme')||'dark';
if(t==='dark')document.documentElement.classList.add('dark');
else document.documentElement.classList.remove('dark');}catch(e){}})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body>
        <ThemeProvider>
          <AuthProvider>
            <Navbar />
            <main className="pt-6 px-4">
              <div className="mx-auto max-w-6xl">{children}</div>
            </main>
            <Footer />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
