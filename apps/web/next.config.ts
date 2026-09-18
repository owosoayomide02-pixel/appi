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
};

export default nextConfig;
