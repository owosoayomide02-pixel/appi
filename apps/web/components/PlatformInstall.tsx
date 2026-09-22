"use client";

import { API_URL } from "@/lib/env";
import { detectPlatform, platformFromQuery, type PlatformId } from "@/lib/platform";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Asset = {
  id: PlatformId | string;
  label: string;
  kind: string;
  url: string;
  filename: string;
  available: boolean;
  blurb: string;
  pair_template: string;
};

type Manifest = {
  detected: string;
  recommended: Asset;
  platforms: Asset[];
};

type Props = {
  preferred?: string | null;
  showAll?: boolean;
  compact?: boolean;
  pairingCode?: string;
};

function pairCommand(template: string, code: string): string {
  return (template || "pair --code {code}").replace("{code}", code || "123456");
}

const FALLBACK_PLATFORMS: Asset[] = [
  {
    id: "windows",
    label: "Windows",
    kind: "exe",
    url: "https://github.com/owosoayomide02-pixel/appi/releases/download/v0.4.0/Appi-windows.zip",
    filename: "Appi-windows.zip",
    available: true,
    blurb: "Download the Appi desktop app (zip). Unzip, open Appi.exe, then pair with a Devices code.",
    pair_template: "Appi.exe pair --code {code}",
  },
  {
    id: "macos",
    label: "macOS",
    kind: "macos",
    url: "https://raw.githubusercontent.com/owosoayomide02-pixel/appi/main/scripts/setup-macos.sh",
    filename: "setup-macos.sh",
    available: true,
    blurb: "Run the macOS setup script — installs Appi, connects to the live site, then pair.",
    pair_template: "python3 -m app.main pair --code {code}",
  },
  {
    id: "linux",
    label: "Linux",
    kind: "linux",
    url: "https://raw.githubusercontent.com/owosoayomide02-pixel/appi/main/scripts/setup-linux.sh",
    filename: "setup-linux.sh",
    available: true,
    blurb: "Run the Linux setup script — installs Appi, connects to the live site, then pair.",
    pair_template: "python3 -m app.main pair --code {code}",
  },
];

function withFallbackUrls(platforms: Asset[]): Asset[] {
  return platforms.map((p) => {
    if (p.url) return p;
    const fb = FALLBACK_PLATFORMS.find((f) => f.id === p.id);
    return fb ? { ...p, url: fb.url, available: true } : p;
  });
}

export function PlatformInstall({ preferred, showAll = true, compact = false, pairingCode }: Props) {
  const [os, setOs] = useState<PlatformId>("unknown");
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fromQuery = platformFromQuery(preferred || null);
    setOs(fromQuery || detectPlatform().id);
  }, [preferred]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/downloads`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error(`Could not load installers (${res.status})`);
        const data = (await res.json()) as Manifest;
        if (!cancelled) {
          const platforms = withFallbackUrls(data.platforms || []);
          const recommended =
            platforms.find((p) => p.id === data.recommended?.id) ||
            platforms[0] ||
            FALLBACK_PLATFORMS[0];
          setManifest({
            ...data,
            platforms,
            recommended,
          });
          if (!platformFromQuery(preferred || null) && data.detected && data.detected !== "unknown") {
            setOs(data.detected as PlatformId);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setManifest({
            detected: "unknown",
            recommended: FALLBACK_PLATFORMS[0],
            platforms: FALLBACK_PLATFORMS,
          });
          setError(err instanceof Error ? err.message : "Could not load installers from env");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [preferred]);

  const platforms = manifest?.platforms || [];
  const primary = useMemo(() => {
    const match = platforms.find((p) => p.id === os);
    return match || manifest?.recommended || platforms[0] || null;
  }, [platforms, os, manifest]);

  if (error && !primary) {
    return <p className="text-sm text-[var(--danger)]">{error}</p>;
  }

  if (!primary) {
    return <p className="text-sm text-[var(--fg-muted)]">Loading installer from .env…</p>;
  }

  return (
    <div className={compact ? "space-y-4" : "space-y-6"}>
      <div className="glass rounded-[1.6rem] p-6">
        <p className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">FROM .ENV · DETECTED</p>
        <h2 className="mt-2 text-2xl font-semibold">
          {primary.label}{" "}
          <span className="text-[var(--fg-muted)]">({primary.kind === "exe" ? ".exe" : primary.kind})</span>
        </h2>
        <p className="mt-2 text-sm text-[var(--fg-muted)]">{primary.blurb}</p>
        <div className="mt-5 flex flex-wrap gap-3">
          {primary.url && primary.available !== false ? (
            <a
              href={primary.url}
              className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm text-white"
              download={primary.filename}
              rel="noopener noreferrer"
            >
              Download for {primary.label}
            </a>
          ) : (
            <span className="rounded-full bg-[var(--line)] px-5 py-3 text-sm text-[var(--fg-muted)]">
              Installer not published yet for {primary.label}
            </span>
          )}
          {showAll && platforms.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {platforms.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setOs(p.id as PlatformId)}
                  className={`rounded-full border px-4 py-2 text-xs ${
                    p.id === primary.id ? "border-[var(--accent)] text-[var(--accent)]" : "border-[var(--line)]"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          )}
        </div>
        {pairingCode !== undefined && (
          <pre className="mt-5 overflow-x-auto rounded-2xl bg-black/30 p-4 font-mono text-sm">
            {pairCommand(primary.pair_template, pairingCode)}
          </pre>
        )}
        {error && <p className="mt-3 text-xs text-[var(--fg-muted)]">{error}</p>}
      </div>

      {!compact && (
        <p className="text-sm text-[var(--fg-muted)]">
          Already installed?{" "}
          <Link href="/device" className="text-[var(--accent)]">
            Open Devices to pair
          </Link>{" "}
          or go to the{" "}
          <Link href="/app" className="text-[var(--accent)]">
            operator
          </Link>
          .
        </p>
      )}
    </div>
  );
}
