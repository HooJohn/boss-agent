import type { Metadata } from "next";
import { AppProvider } from "@/context/app-context";
import "./globals.css";
import Providers from "@/providers";
import Header from "@/components/header";
import Footer from "@/components/footer";

export const metadata: Metadata = {
  title: "Boss-Agent",
  description: "智能决策，数据驱动的企业报表与分析AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          rel="apple-touch-icon"
          sizes="180x180"
          href="/favicon/apple-touch-icon.png"
        />
        <link
          rel="icon"
          type="image/png"
          sizes="32x32"
          href="/favicon/favicon-32x32.png"
        />
        <link
          rel="icon"
          type="image/png"
          sizes="16x16"
          href="/favicon/favicon-16x16.png"
        />
        <link rel="manifest" href="/favicon/site.webmanifest" />
      </head>
      <body className={`antialiased flex flex-col h-screen`}>
        <AppProvider>
          <Providers>
            <Header />
            <main className="flex-grow container mx-auto p-4 flex overflow-y-auto">
              {children}
            </main>
            <Footer />
          </Providers>
        </AppProvider>
      </body>
    </html>
  );
}
