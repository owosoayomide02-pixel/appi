import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8 text-center">
      <p className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">APPI</p>
      <h1 className="font-[family-name:var(--font-display)] mt-4 text-4xl">This page is not here.</h1>
      <p className="mt-3 max-w-md text-sm text-[var(--fg-muted)]">The operator only acts on routes that exist. Same rule as tools.</p>
      <Link href="/" className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-sm text-white">
        Back to the website
      </Link>
    </div>
  );
}
