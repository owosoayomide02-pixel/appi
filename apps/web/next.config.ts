import path from "path";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// Load monorepo root `.env` first, then apps/web `.env*` (local wins).
const webDir = __dirname;
const repoRoot = path.join(webDir, "..", "..");
loadEnvConfig(repoRoot);
loadEnvConfig(webDir);

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    return [{ source: "/health-proxy", destination: `${api}/api/v1/health` }];
  },
  env: {
    NEXT_PUBLIC_APP_URL:
      process.env.NEXT_PUBLIC_APP_URL || process.env.APP_URL || "http://localhost:3000",
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
    NEXT_PUBLIC_GITHUB_REPO:
      process.env.NEXT_PUBLIC_GITHUB_REPO || process.env.GITHUB_REPO || "owosoayomide02-pixel/appi",
    NEXT_PUBLIC_DOWNLOAD_WINDOWS_URL: process.env.NEXT_PUBLIC_DOWNLOAD_WINDOWS_URL || "",
    NEXT_PUBLIC_DOWNLOAD_MACOS_URL: process.env.NEXT_PUBLIC_DOWNLOAD_MACOS_URL || "",
    NEXT_PUBLIC_DOWNLOAD_LINUX_URL: process.env.NEXT_PUBLIC_DOWNLOAD_LINUX_URL || "",
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || "",
    NEXT_PUBLIC_SUPABASE_ANON_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      process.env.SUPABASE_ANON_KEY ||
      "",
  },
};

export default nextConfig;
