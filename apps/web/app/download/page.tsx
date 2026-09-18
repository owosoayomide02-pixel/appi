import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Download",
  description: "Install the Appi Windows operator, pair this device, and start the dashboard.",
};

const steps = [
  {
    title: "Create an APPI account",
    body: "Register in the browser, then complete onboarding. You will choose folders Appi may touch and the initial ALLOW / ASK / BLOCK policy.",
  },
  {
    title: "Install the Windows runtime",
    body: "Prefer the Desktop Appi shortcut from python -m app.main install in the device-agent folder. Or double-click Appi.exe from the Windows package. Do not Run as administrator.",
  },
  {
    title: "Pair once",
    body: "Open Devices in the operator, generate a six-digit code, then run Appi.exe pair --code 123456 (no brackets). After that, start Appi normally.",
  },
  {
    title: "Talk or type",
    body: "Say Appi, wait for the greeting, then a short command such as “open Chrome”. Ctrl+Shift+A if the wake word misses. Closing the window leaves the assistant in the tray.",
  },
];

export default function DownloadPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-4xl px-5 py-16">
        <p className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">DOWNLOAD</p>
        <h1 className="font-[family-name:var(--font-display)] mt-4 text-4xl tracking-tight md:text-6xl">Windows first. Honest everywhere else.</h1>
        <p className="mt-5 max-w-2xl text-lg text-[var(--fg-muted)]">
          The working assistant is the Windows background runtime plus this website’s operator. Android and iOS shells exist as placeholders and return CAPABILITY_UNAVAILABLE for unsupported actions.
        </p>

        <div className="mt-10 flex flex-wrap gap-3">
          <Link href="/register" className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm text-white">
            Get started in the browser
          </Link>
          <Link href="/app" className="rounded-full border border-[var(--line)] px-5 py-3 text-sm">
            Open operator
          </Link>
        </div>

        <ol className="mt-14 space-y-4">
          {steps.map((step, i) => (
            <li key={step.title} className="glass rounded-[1.6rem] p-6">
              <div className="font-mono text-xs text-[var(--fg-muted)]">STEP {i + 1}</div>
              <h2 className="mt-2 text-xl">{step.title}</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--fg-muted)]">{step.body}</p>
            </li>
          ))}
        </ol>

        <pre className="glass mt-10 overflow-x-auto rounded-[1.6rem] p-5 font-mono text-sm">
{`cd apps\\device-agent
python -m app.main install
python -m app.main pair --code 482917`}
        </pre>
        <p className="mt-4 text-sm text-[var(--fg-muted)]">
          Developers can also run the API on port 8000 and this Next.js site on port 3000. Pairing still happens from Devices.
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
