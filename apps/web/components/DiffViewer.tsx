"use client";

export function DiffViewer({ path, before, after }: { path: string; before: string; after: string }) {
  return (
    <section className="glass rounded-3xl p-6">
      <div className="text-xs tracking-[0.2em] text-[var(--fg-muted)]">DIFF</div>
      <div className="mt-1 font-mono text-sm">{path}</div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <pre className="max-h-80 overflow-auto rounded-2xl bg-black/20 p-4 text-xs text-red-300">{before || "(empty)"}</pre>
        <pre className="max-h-80 overflow-auto rounded-2xl bg-black/20 p-4 text-xs text-emerald-300">{after || "(empty)"}</pre>
      </div>
    </section>
  );
}
