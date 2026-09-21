"use client";

import { API_URL } from "@/lib/api";
import { useEffect, useState } from "react";

type Providers = { github: boolean; google: boolean };

export function OAuthButtons({ mode }: { mode: "login" | "register" }) {
  const [providers, setProviders] = useState<Providers>({ github: false, google: false });

  useEffect(() => {
    fetch(`${API_URL}/api/v1/auth/oauth/providers`)
      .then((r) => (r.ok ? r.json() : { github: false, google: false }))
      .then((data: Providers) => setProviders(data))
      .catch(() => setProviders({ github: false, google: false }));
  }, []);

  const label = mode === "login" ? "Sign in" : "Continue";

  if (!providers.github && !providers.google) {
    return (
      <p className="mt-4 text-xs text-slate-500">
        GitHub / Google sign-in appears once OAuth apps are configured on the API.
      </p>
    );
  }

  return (
    <div className="mt-6 space-y-3">
      <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-slate-500">
        <span className="h-px flex-1 bg-cyan-500/20" />
        or
        <span className="h-px flex-1 bg-cyan-500/20" />
      </div>
      {providers.github && (
        <a
          href={`${API_URL}/api/v1/auth/oauth/github/start`}
          className="flex w-full items-center justify-center gap-2 rounded-full border border-cyan-400/35 bg-white/5 px-4 py-3 text-sm text-white transition hover:border-cyan-300/60 hover:bg-white/10"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current" aria-hidden>
            <path d="M12 .5C5.73.5.5 5.74.5 12.02c0 5.1 3.29 9.42 7.86 10.95.58.11.79-.25.79-.56 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.3-1.7-1.3-1.7-1.06-.73.08-.72.08-.72 1.17.08 1.79 1.2 1.79 1.2 1.04 1.78 2.73 1.27 3.4.97.11-.75.41-1.27.74-1.56-2.55-.29-5.23-1.28-5.23-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 2.9-.39c.98 0 1.97.13 2.9.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.18 1.84 1.18 3.1 0 4.42-2.69 5.39-5.25 5.67.42.36.79 1.08.79 2.18 0 1.57-.01 2.84-.01 3.23 0 .31.21.68.8.56A10.52 10.52 0 0 0 23.5 12C23.5 5.74 18.27.5 12 .5Z" />
          </svg>
          {label} with GitHub
        </a>
      )}
      {providers.google && (
        <a
          href={`${API_URL}/api/v1/auth/oauth/google/start`}
          className="flex w-full items-center justify-center gap-2 rounded-full border border-cyan-400/35 bg-white/5 px-4 py-3 text-sm text-white transition hover:border-cyan-300/60 hover:bg-white/10"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
            <path fill="#EA4335" d="M12 10.2v3.6h5.1c-.2 1.2-.9 2.3-1.9 3l3.1 2.4c1.8-1.7 2.9-4.1 2.9-7 0-.7-.1-1.3-.2-1.9H12z" />
            <path fill="#34A853" d="M6.6 14.3l-.9.7-2.5 1.9C4.8 19.7 8.1 22 12 22c2.7 0 5-.9 6.7-2.4l-3.1-2.4c-.9.6-2 1-3.6 1-2.8 0-5.1-1.9-6-4.4z" />
            <path fill="#4A90E2" d="M3.2 7.1C2.4 8.6 2 10.2 2 12s.4 3.4 1.2 4.9l3.4-2.6C6.2 13.4 6 12.7 6 12s.2-1.4.6-2.3L3.2 7.1z" />
            <path fill="#FBBC05" d="M12 6c1.5 0 2.9.5 4 1.5l3-3C16.9 2.9 14.7 2 12 2 8.1 2 4.8 4.3 3.2 7.1l3.4 2.6C7 7.9 9.2 6 12 6z" />
          </svg>
          {label} with Google
        </a>
      )}
    </div>
  );
}
