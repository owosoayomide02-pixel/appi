"use client";

import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import { Device } from "@/lib/types";
import { useEffect, useState } from "react";

type Health = {
  ok: boolean;
  ai_provider: string;
  ai_configured: boolean;
  ai_model: string | null;
  ai_last_error?: string | null;
  supabase_configured?: boolean;
};

export default function SettingsPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [ttsVoice, setTtsVoice] = useState("");
  const [culture, setCulture] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Health>("/api/v1/health")
      .then(setHealth)
      .catch(() => undefined);
    api<Device[]>("/api/v1/devices")
      .then((rows) => {
        setDevices(rows);
        const first = rows.find((row) => !row.revoked) || rows[0];
        if (first) {
          setDeviceId(first.id);
          setTtsVoice(first.voice?.tts_voice || "");
          setCulture(first.voice?.culture || "");
        }
      })
      .catch(() => undefined);
  }, []);

  const selected = devices.find((row) => row.id === deviceId);
  const voices = selected?.voice?.voices || [];
  const recognizers = selected?.voice?.recognizers || [];

  async function saveVoice() {
    if (!deviceId) return;
    setBusy(true);
    try {
      const result = await api<{ applied: boolean }>("/api/v1/devices/" + deviceId + "/voice", {
        method: "PATCH",
        body: JSON.stringify({ tts_voice: ttsVoice, culture }),
      });
      setMessage(
        result.applied
          ? "Voice preference sent to the device."
          : "Saved. Restart serve --voice (or wait for reconnect) so the device picks it up.",
      );
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not save voice preference");
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    await api("/api/v1/auth/logout", { method: "POST" });
    window.location.href = "/";
  }

  return (
    <AppShell>
      <h1 className="mb-2 text-3xl font-semibold">Settings</h1>
      <section className="glass mb-4 max-w-xl rounded-3xl p-6">
        <h2 className="text-lg">Voice</h2>
        <p className="mt-2 text-sm text-[var(--fg-muted)]">
          Speaking voice and recognition language come from Windows on this PC. Start `serve --voice` so the installed voices appear. After Yes?, speak a short command such as “open Chrome”.
        </p>
        {devices.length > 1 ? (
          <select
            value={deviceId}
            onChange={(e) => {
              const next = devices.find((row) => row.id === e.target.value);
              setDeviceId(e.target.value);
              setTtsVoice(next?.voice?.tts_voice || "");
              setCulture(next?.voice?.culture || "");
            }}
            className="mt-4 w-full rounded-2xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
          >
            {devices.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name}
              </option>
            ))}
          </select>
        ) : null}
        <label className="mt-4 block text-xs uppercase tracking-[0.2em] text-[var(--fg-muted)]">Speaking voice</label>
        <select
          value={ttsVoice}
          onChange={(e) => setTtsVoice(e.target.value)}
          className="mt-2 w-full rounded-2xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
        >
          <option value="">Windows default</option>
          {voices.map((voice) => (
            <option key={voice.name} value={voice.name}>
              {voice.name} ({voice.gender} · {voice.culture})
            </option>
          ))}
        </select>
        <label className="mt-4 block text-xs uppercase tracking-[0.2em] text-[var(--fg-muted)]">Recognition language</label>
        <select
          value={culture}
          onChange={(e) => setCulture(e.target.value)}
          className="mt-2 w-full rounded-2xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
        >
          <option value="">Windows default</option>
          {recognizers.map((row) => (
            <option key={row.id || row.culture} value={row.culture}>
              {row.name} ({row.culture})
            </option>
          ))}
        </select>
        {voices.length === 0 ? (
          <p className="mt-3 text-xs text-[var(--fg-muted)]">No voices listed yet. Keep the device runtime online, then refresh this page.</p>
        ) : null}
        <button disabled={busy || !deviceId} onClick={saveVoice} className="mt-4 rounded-full border border-[var(--line)] px-4 py-2 text-sm">
          Save voice
        </button>
        {message ? <p className="mt-3 text-sm text-sky-300">{message}</p> : null}
      </section>
      <section className="glass mb-4 max-w-xl rounded-3xl p-6">
        <h2 className="text-lg">Planner</h2>
        <p className="mt-2 text-sm text-[var(--fg-muted)]">
          {health?.ai_configured
            ? `Using ${health.ai_provider}${health.ai_model ? ` (${health.ai_model})` : ""}. Guardian still authorizes every action.`
            : "Heuristic planner is active. Set AI_PROVIDER and AI_API_KEY (or OPENAI_API_KEY) to use a model."}
        </p>
        {health?.ai_last_error && (
          <p className="mt-3 rounded-2xl border border-[var(--warn)]/40 bg-[var(--warn)]/10 p-3 text-xs">{health.ai_last_error}</p>
        )}
      </section>
      <section className="glass mb-4 max-w-xl rounded-3xl p-6">
        <h2 className="text-lg">Supabase</h2>
        <p className="mt-2 text-sm text-[var(--fg-muted)]">
          {health?.supabase_configured
            ? "Project keys are loaded from the server environment. The service role stays encrypted and is never sent to the model."
            : "Not configured. Add SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY to .env."}
        </p>
      </section>
      <section className="glass max-w-xl rounded-3xl p-6">
        <h2 className="text-lg">Security</h2>
        <p className="mt-2 text-sm text-[var(--fg-muted)]">
          Passwords are hashed. Secrets use handles such as secret://github/token/main. The kill switch does not go through the model.
        </p>
        <button onClick={logout} className="mt-6 rounded-full border border-[var(--line)] px-4 py-2 text-sm">
          Sign out
        </button>
      </section>
    </AppShell>
  );
}
