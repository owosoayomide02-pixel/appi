import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--line)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 py-10 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="font-[family-name:var(--font-display)] text-sm tracking-[0.22em]">APPI</div>
          <p className="mt-2 max-w-sm text-sm text-[var(--fg-muted)]">Think. Act. Verify. A persistent AI operator from MELIX STUDIOS.</p>
        </div>
        <nav className="flex flex-wrap gap-5 text-sm text-[var(--fg-muted)]">
          <Link href="/product">Product</Link>
          <Link href="/security">Security</Link>
          <Link href="/download">Download</Link>
          <Link href="/login">Operator</Link>
        </nav>
      </div>
    </footer>
  );
}
