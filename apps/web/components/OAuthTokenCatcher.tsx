"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

/**
 * After OAuth redirect, API may pass access_token in the query (cross-site cookie fallback).
 */
export function OAuthTokenCatcher() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = params.get("access_token");
    if (!token) return;
    try {
      localStorage.setItem("appi_access_token", token);
    } catch {
      /* ignore */
    }
    const next = new URLSearchParams(params.toString());
    next.delete("access_token");
    next.delete("oauth");
    const qs = next.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  }, [params, pathname, router]);

  return null;
}
