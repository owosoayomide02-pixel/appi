"use client";

import { AppShell } from "@/components/AppShell";
import { api, API_URL } from "@/lib/api";
import { Connection } from "@/lib/types";
import { useEffect, useState } from "react";

const CATEGORIES = ["developer", "cloud", "communication", "social", "productivity", "payments", "finance", "shopping"];

const STATUS_LABEL: Record<Connection["status"], string> = {
  connected: "Connected",
  not_connected: "Not connected",
  permission_required: "Permission required",
  unsupported: "Unsupported",
};

export default function ConnectionsPage() {
  const [rows, setRows] = useState<Connection[]>([]);
  const [token, setToken] = useState("");
  const [gmailToken, setGmailToken] = useState("");
  const [calendarToken, setCalendarToken] = useState("");
  const [device, setDevice] = useState<{ user_code?: string; verification_uri?: string } | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = () => api<Connection[]>("/api/v1/connections").then(setRows).catch(() => undefined);

  useEffect(() => {
    refresh();
  }, []);

  return (
    <AppShell>
      <h1 className="mb-2 text-3xl font-semibold">Connections</h1>
      <p className="mb-6 text-sm text-[var(--fg-muted)]">
        Official API / OAuth first. Nothing is shown as connected without a verified credential.
      </p>
      {message ? <p className="mb-4 text-sm text-sky-300">{message}</p> : null}
      {CATEGORIES.map((category) => {
        const items = rows.filter((row) => row.category === category);
        if (items.length === 0) return null;
        return (
          <section key={category} className="mb-8">
            <h2 className="mb-3 text-sm uppercase tracking-[0.2em] text-[var(--fg-muted)]">{category}</h2>
            <div className="grid gap-3 md:grid-cols-2">
              {items.map((row) => (
                <article key={row.provider} className="glass rounded-3xl p-5">
                  <div className="text-lg">{row.name}</div>
                  <div className="mt-1 text-sm text-[var(--fg-muted)]">
                    {STATUS_LABEL[row.status]}
                    {row.account ? ` · ${row.account}` : ""}
                  </div>
                  {row.provider === "github" ? (
                    <GitHubPanel
                      row={row}
                      token={token}
                      setToken={setToken}
                      device={device}
                      setDevice={setDevice}
                      busy={busy}
                      setBusy={setBusy}
                      setMessage={setMessage}
                      onDone={refresh}
                    />
                  ) : row.provider === "gmail" ? (
                    <GmailPanel
                      row={row}
                      token={gmailToken}
                      setToken={setGmailToken}
                      busy={busy}
                      setBusy={setBusy}
                      setMessage={setMessage}
                      onDone={refresh}
                    />
                  ) : row.provider === "google_calendar" ? (
                    <CalendarPanel
                      row={row}
                      token={calendarToken}
                      setToken={setCalendarToken}
                      busy={busy}
                      setBusy={setBusy}
                      setMessage={setMessage}
                      onDone={refresh}
                    />
                  ) : (
                    <button disabled className="mt-4 rounded-full border border-[var(--line)] px-4 py-2 text-xs text-[var(--fg-muted)]">
                      {row.status === "connected"
                        ? "Connected"
                        : row.status === "unsupported"
                          ? "Unavailable on this platform"
                          : row.oauth
                            ? "Connect (OAuth not configured)"
                            : "Not configured"}
                    </button>
                  )}
                </article>
              ))}
            </div>
          </section>
        );
      })}
    </AppShell>
  );
}

function GitHubPanel({
  row,
  token,
  setToken,
  device,
  setDevice,
  busy,
  setBusy,
  setMessage,
  onDone,
}: {
  row: Connection;
  token: string;
  setToken: (value: string) => void;
  device: { user_code?: string; verification_uri?: string } | null;
  setDevice: (value: { user_code?: string; verification_uri?: string } | null) => void;
  busy: boolean;
  setBusy: (value: boolean) => void;
  setMessage: (value: string) => void;
  onDone: () => void;
}) {
  async function connectToken() {
    setBusy(true);
    try {
      const result = await api<{ login: string }>("/api/v1/connections/github/token", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setToken("");
      setMessage(`GitHub connected as ${result.login}`);
      onDone();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "GitHub connect failed");
    } finally {
      setBusy(false);
    }
  }

  async function startDevice() {
    setBusy(true);
    try {
      const result = await api<{ user_code: string; verification_uri: string }>("/api/v1/connections/github/oauth/device", {
        method: "POST",
      });
      setDevice(result);
      setMessage(`Enter ${result.user_code} at ${result.verification_uri}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "GitHub OAuth is not configured");
    } finally {
      setBusy(false);
    }
  }

  async function pollDevice() {
    setBusy(true);
    try {
      const result = await api<{ status: string; login?: string; error?: string }>("/api/v1/connections/github/oauth/device/poll", {
        method: "POST",
      });
      if (result.status === "connected") {
        setDevice(null);
        setMessage(`GitHub connected as ${result.login}`);
        onDone();
      } else {
        setMessage(result.error === "authorization_pending" ? "Waiting for GitHub approval…" : result.error || result.status);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Poll failed");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    try {
      await api("/api/v1/connections/github", { method: "DELETE" });
      setMessage("GitHub disconnected");
      onDone();
    } finally {
      setBusy(false);
    }
  }

  if (row.connected) {
    return (
      <button disabled={busy} onClick={disconnect} className="mt-4 rounded-full border border-[var(--line)] px-4 py-2 text-xs">
        Disconnect
      </button>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      {row.oauth_ready ? (
        <div className="flex flex-wrap gap-2">
          <a className="rounded-full border border-[var(--line)] px-4 py-2 text-xs" href={`${API_URL}/api/v1/connections/github/oauth/start`}>
            Connect with GitHub
          </a>
          <button disabled={busy} onClick={startDevice} className="rounded-full border border-[var(--line)] px-4 py-2 text-xs">
            Device code
          </button>
          {device ? (
            <button disabled={busy} onClick={pollDevice} className="rounded-full border border-[var(--line)] px-4 py-2 text-xs">
              I authorized it
            </button>
          ) : null}
        </div>
      ) : (
        <p className="text-xs text-[var(--fg-muted)]">OAuth app not configured. Paste a GitHub PAT with `read:user` (and `repo` to list private repos). Appi verifies it against api.github.com before marking connected.</p>
      )}
      <input
        type="password"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="ghp_…"
        className="w-full rounded-2xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
      />
      <button disabled={busy || token.length < 8} onClick={connectToken} className="rounded-full border border-[var(--line)] px-4 py-2 text-xs">
        Verify and connect
      </button>
    </div>
  );
}

function GmailPanel({
  row,
  token,
  setToken,
  busy,
  setBusy,
  setMessage,
  onDone,
}: {
  row: Connection;
  token: string;
  setToken: (value: string) => void;
  busy: boolean;
  setBusy: (value: boolean) => void;
  setMessage: (value: string) => void;
  onDone: () => void;
}) {
  async function connectToken() {
    setBusy(true);
    try {
      const result = await api<{ email: string }>("/api/v1/connections/gmail/token", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setToken("");
      setMessage(`Gmail connected as ${result.email}`);
      onDone();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Gmail connect failed");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    try {
      await api("/api/v1/connections/gmail", { method: "DELETE" });
      setMessage("Gmail disconnected. Calendar and Contacts were not connected.");
      onDone();
    } finally {
      setBusy(false);
    }
  }

  if (row.connected) {
    return (
      <button disabled={busy} onClick={disconnect} className="mt-4 rounded-full border border-[var(--line)] px-4 py-2 text-xs">
        Disconnect
      </button>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      {row.oauth_ready ? (
        <a className="inline-block rounded-full border border-[var(--line)] px-4 py-2 text-xs" href={`${API_URL}/api/v1/connections/gmail/oauth/start`}>
          Connect with Google
        </a>
      ) : (
        <p className="text-xs text-[var(--fg-muted)]">
          OAuth app not configured. Paste a Google access token with Gmail scopes. Appi calls Gmail users.me/profile before marking connected. This does not connect Calendar or Contacts.
        </p>
      )}
      <input
        type="password"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="ya29.…"
        className="w-full rounded-2xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
      />
      <button disabled={busy || token.length < 8} onClick={connectToken} className="rounded-full border border-[var(--line)] px-4 py-2 text-xs">
        Verify and connect
      </button>
    </div>
  );
}

function CalendarPanel({
  row,
  token,
  setToken,
  busy,
  setBusy,
  setMessage,
  onDone,
}: {
  row: Connection;
  token: string;
  setToken: (value: string) => void;
  busy: boolean;
  setBusy: (value: boolean) => void;
  setMessage: (value: string) => void;
  onDone: () => void;
}) {
  async function connectToken() {
    setBusy(true);
    try {
      const result = await api<{ email: string }>("/api/v1/connections/google_calendar/token", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setToken("");
      setMessage(`Google Calendar connected as ${result.email}`);
      onDone();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Calendar connect failed");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    try {
      await api("/api/v1/connections/google_calendar", { method: "DELETE" });
      setMessage("Google Calendar disconnected. Gmail and Contacts were not connected.");
      onDone();
    } finally {
      setBusy(false);
    }
  }

  if (row.connected) {
    return (
      <button disabled={busy} onClick={disconnect} className="mt-4 rounded-full border border-[var(--line)] px-4 py-2 text-xs">
        Disconnect
      </button>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      {row.oauth_ready ? (
        <a className="inline-block rounded-full border border-[var(--line)] px-4 py-2 text-xs" href={`${API_URL}/api/v1/connections/google_calendar/oauth/start`}>
          Connect Google Calendar
        </a>
      ) : (
        <p className="text-xs text-[var(--fg-muted)]">
          OAuth app not configured. Paste a Google access token with Calendar scopes. Appi calls calendarList before marking connected. This does not connect Gmail or Contacts.
        </p>
      )}
      <input
        type="password"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="ya29.…"
        className="w-full rounded-2xl border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
      />
      <button disabled={busy || token.length < 8} onClick={connectToken} className="rounded-full border border-[var(--line)] px-4 py-2 text-xs">
        Verify and connect
      </button>
    </div>
  );
}
