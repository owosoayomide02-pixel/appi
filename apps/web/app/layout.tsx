import type { Metadata } from "next";
import { Suspense } from "react";
import { IBM_Plex_Mono, Orbitron, Sora } from "next/font/google";
import { OceanField } from "@/components/marketing/OceanField";
import { OAuthTokenCatcher } from "@/components/OAuthTokenCatcher";
import { APP_URL } from "@/lib/env";
import "./globals.css";

const display = Orbitron({ variable: "--font-display", subsets: ["latin"] });
const body = Sora({ variable: "--font-body", subsets: ["latin"] });
const mono = IBM_Plex_Mono({ variable: "--font-mono", subsets: ["latin"], weight: ["400", "500"] });

export const metadata: Metadata = {
  metadataBase: new URL(APP_URL),
  title: { default: "APPI — Tell it what you need done", template: "%s · APPI" },
  description: "Think. Act. Verify. A persistent AI operator with Guardian, real tools, and an audit trail.",
  icons: { icon: "/appi-mark.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className={`${display.variable} ${body.variable} ${mono.variable} antialiased`}>
        <OceanField />
        <div className="relative z-10">
          <Suspense fallback={null}>
            <OAuthTokenCatcher />
          </Suspense>
          {children}
        </div>
      </body>
    </html>
  );
}
