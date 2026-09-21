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
          setManifest(data);
          if (!platformFromQuery(preferred || null) && data.detected && data.detected !== "unknown") {
            setOs(data.detected as PlatformId);
          }
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load installers from env");
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
          <a
            href={primary.url}
            className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm text-white"
            download={primary.filename}
          >
            Download for {primary.label}
          </a>
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
