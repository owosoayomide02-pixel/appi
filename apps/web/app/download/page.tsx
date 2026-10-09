import { DownloadClient } from "./DownloadClient";
import type { Metadata } from "next";
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "Download",
  description: "Install Appi for Windows, macOS, or Linux — auto-detected from your device.",
};

export default function DownloadPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-sm text-[var(--fg-muted)]">Loading…</div>
      }
    >
      <DownloadClient />
    </Suspense>
  );
}
