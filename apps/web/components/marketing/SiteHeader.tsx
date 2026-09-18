"use client";

import { api } from "@/lib/api";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const links = [
  { href: "/product", label: "Product" },
  { href: "/security", label: "Security" },
  { href: "/download", label: "Download" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    api<{ id: string }>("/api/v1/auth/me")
      .then(() => setSignedIn(true))
      .catch(() => setSignedIn(false));
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--bg)_78%,transparent)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Link href="/" className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/appi-mark.svg" alt="" width={32} height={32} />
          <span className="font-[family-name:var(--font-display)] text-lg tracking-[0.18em]">APPI</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-[var(--fg-muted)] md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? "text-[var(--fg)]" : "hover:text-[var(--fg)]"}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="hidden items-center gap-3 md:flex">
          {signedIn ? (
            <Link href="/app" className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm text-white">
              Open operator
            </Link>
          ) : (
            <>
              <Link href="/login" className="text-sm text-[var(--fg-muted)] hover:text-[var(--fg)]">
                Sign in
              </Link>
              <Link href="/register" className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm text-white">
                Get started
              </Link>
            </>
          )}
        </div>
        <button className="rounded-full border border-[var(--line)] p-2 md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Menu">
          {open ? <X size={16} /> : <Menu size={16} />}
        </button>
      </div>
      {open && (
        <div className="border-t border-[var(--line)] px-5 py-4 md:hidden">
          <div className="flex flex-col gap-3 text-sm">
            {links.map((link) => (
              <Link key={link.href} href={link.href}>
                {link.label}
              </Link>
            ))}
            <Link href={signedIn ? "/app" : "/login"}>{signedIn ? "Open operator" : "Sign in"}</Link>
          </div>
        </div>
      )}
    </header>
  );
}
