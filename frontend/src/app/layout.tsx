import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "UcuncuGoz — Arac Tespit",
  description: "Bulut tabanli arac tespit ve trafik analiz sistemi",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr" className={cn("font-sans", inter.variable)}>
      <body className="antialiased bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
