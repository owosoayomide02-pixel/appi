"use client";

import { PlatformInstall } from "@/components/PlatformInstall";
import { api } from "@/lib/api";
import { detectPlatform, platformFromQuery } from "@/lib/platform";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

const STEPS = ["Welcome", "Install", "Pair device", "Folders", "Permissions", "Test", "Dashboard"];

function OnboardingForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [step, setStep] = useState(0);
  const [code, setCode] = useState<string>("");
  const [folder, setFolder] = useState("");
  const [folders, setFolders] = useState<{ id: string; path: string }[]>([]);
  const [osLabel, setOsLabel] = useState("your device");
  const [preferredOs, setPreferredOs] = useState<string | null>(null);
  const [folderHint, setFolderHint] = useState("~/Projects");
  const [policy, setPolicy] = useState({
    read_project_files: "ALLOW",
    edit_project_files: "ASK",
    run_tests: "ALLOW",
    run_terminal: "ASK",
    use_browser: "ASK",
    delete_files: "ASK",
  });
  const [test, setTest] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fromQuery = platformFromQuery(params.get("os"));
    const p = fromQuery
      ? {
          id: fromQuery,
          label: fromQuery === "windows" ? "Windows" : fromQuery === "macos" ? "macOS" : "Linux",
        }
      : detectPlatform();
    setPreferredOs(p.id === "unknown" ? null : p.id);
    setOsLabel(p.label);
    setFolderHint(p.id === "windows" ? "C:\\Users\\You\\Projects" : "~/Projects");
  }, [params]);

  async function startPair() {
    const data = await api<{ pairing_code: string }>("/api/v1/devices/pair/start", { method: "POST" });
    setCode(data.pairing_code);
  }

  async function addFolder() {
    setError("");
    try {
      await api("/api/v1/onboarding/folders", { method: "POST", body: JSON.stringify({ path: folder }) });
      setFolders(await api("/api/v1/onboarding/folders"));
      setFolder("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Folder rejected");
    }
  }

  async function savePolicy() {
    await api("/api/v1/permissions/policy", { method: "PUT", body: JSON.stringify(policy) });
    setStep(5);
  }

  async function testConnection() {
    setTest(await api("/api/v1/onboarding/connection-test"));
  }

  async function finish() {
    await api("/api/v1/onboarding/complete", { method: "POST", body: JSON.stringify({ theme: "dark" }) });
    router.push("/app");
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center p-6">
      <div className="text-xs tracking-[0.28em] text-[var(--fg-muted)]">
        STEP {step + 1} / 7 · {STEPS[step]} · {osLabel}
      </div>
      <div className="glass mt-4 rounded-[2rem] p-8">
        {step === 0 && (
          <>
            <h1 className="text-4xl font-semibold">Welcome to Appi.</h1>
            <p className="mt-3 text-[var(--fg-muted)]">
              An AI action layer for {osLabel}. It plans, asks, acts, and verifies — never with full-drive access.
            </p>
            <button className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-white" onClick={() => setStep(1)}>
              Begin
            </button>
          </>
        )}
        {step === 1 && (
          <>
            <h1 className="text-3xl font-semibold">Install for {osLabel}</h1>
            <p className="mt-3 text-[var(--fg-muted)]">
              We detected your OS. Download the matching installer, then continue to pair.
            </p>
            <div className="mt-6">
              <PlatformInstall preferred={preferredOs} compact showAll />
            </div>
            <button
              className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-white"
              onClick={() => {
                setStep(2);
                void startPair();
              }}
            >
              I installed Appi — pair next
            </button>
          </>
        )}
        {step === 2 && (
          <>
            <h1 className="text-3xl font-semibold">Pair this device</h1>
            <p className="mt-3 text-[var(--fg-muted)]">Use the command for {osLabel}:</p>
            <div className="mt-4">
              <PlatformInstall preferred={preferredOs} compact showAll={false} pairingCode={code || "------"} />
            </div>
            <p className="mt-3 text-4xl font-mono tracking-[0.3em]">{code || "------"}</p>
            <button className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-white" onClick={() => setStep(3)}>
              Continue
            </button>
          </>
        )}
        {step === 3 && (
          <>
            <h1 className="text-3xl font-semibold">Approved folders</h1>
            <p className="mt-3 text-[var(--fg-muted)]">
              Appi cannot see your whole drive. Add project folders only. System paths are blocked.
            </p>
            <div className="mt-4 flex gap-2">
              <input
                className="flex-1 rounded-2xl border border-[var(--line)] bg-transparent px-4 py-3"
                placeholder={folderHint}
                value={folder}
                onChange={(e) => setFolder(e.target.value)}
              />
              <button onClick={addFolder} className="rounded-full border border-[var(--line)] px-4">
                Add
              </button>
            </div>
            {error && <p className="mt-2 text-sm text-[var(--danger)]">{error}</p>}
            <ul className="mt-4 space-y-2 text-sm">
              {folders.map((f) => (
                <li key={f.id}>{f.path}</li>
              ))}
            </ul>
            <button className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-white" onClick={() => setStep(4)}>
              Continue
            </button>
          </>
        )}
        {step === 4 && (
          <>
            <h1 className="text-3xl font-semibold">Initial permissions</h1>
            <div className="mt-4 space-y-3">
              {Object.entries(policy).map(([key, value]) => (
                <label key={key} className="flex items-center justify-between gap-4 text-sm">
                  <span>{key.replaceAll("_", " ")}</span>
                  <select
                    className="rounded-full border border-[var(--line)] bg-transparent px-3 py-1"
                    value={value}
                    onChange={(e) => setPolicy({ ...policy, [key]: e.target.value })}
                  >
                    <option>ALLOW</option>
                    <option>ASK</option>
                    <option>BLOCK</option>
                  </select>
                </label>
              ))}
            </div>
            <p className="mt-4 text-xs text-[var(--fg-muted)]">
              Delete files always asks at the engine layer even if you choose ALLOW.
            </p>
            <button className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-white" onClick={savePolicy}>
              Save policy
            </button>
          </>
        )}
        {step === 5 && (
          <>
            <h1 className="text-3xl font-semibold">Test connection</h1>
            <button className="mt-6 rounded-full border border-[var(--line)] px-5 py-3" onClick={testConnection}>
              Run test
            </button>
            {test && <pre className="mt-4 rounded-2xl bg-black/30 p-4 text-xs">{JSON.stringify(test, null, 2)}</pre>}
            <button className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-white" onClick={() => setStep(6)}>
              Continue
            </button>
          </>
        )}
        {step === 6 && (
          <>
            <h1 className="text-3xl font-semibold">Open Appi</h1>
            <p className="mt-3 text-[var(--fg-muted)]">
              The dashboard is ready. Stop Appi is always available. Nothing runs with full-drive access.
            </p>
            <button className="mt-8 rounded-full bg-[var(--accent)] px-5 py-3 text-white" onClick={finish}>
              Open dashboard
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <Suspense
      fallback={<div className="flex min-h-screen items-center justify-center text-sm text-[var(--fg-muted)]">Loading…</div>}
    >
      <OnboardingForm />
    </Suspense>
  );
}
