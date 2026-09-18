import type { Metadata } from "next";
import { Geist, Geist_Mono, Syne } from "next/font/google";
import { APP_URL } from "@/lib/env";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(APP_URL),
  title: {
    default: "APPI — Tell it what you need done",
    template: "%s · APPI",
  },
  description:
    "Think. Act. Verify. A persistent AI operator that plans, asks before sensitive actions, uses real tools, and keeps an audit trail.",
  icons: { icon: "/appi-mark.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} ${syne.variable} antialiased`}>{children}</body>
    </html>
  );
}
