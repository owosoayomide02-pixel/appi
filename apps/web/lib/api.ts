import { API_URL } from "./env";

export { API_URL, APP_URL } from "./env";

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(formatDetail(detail, response.status));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function formatDetail(detail: unknown, status: number): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          const row = item as { msg?: string; loc?: unknown[] };
          const field = Array.isArray(row.loc) ? row.loc.filter((p) => p !== "body").join(".") : "";
          const msg = (row.msg || "").replace(/^Value error, /, "");
          if (msg) return field ? `${field}: ${msg}` : msg;
        }
        return "";
      })
      .filter(Boolean);
    if (messages.length) return messages.join(" · ");
  }
  return `Request failed (${status})`;
}

export function wsUrl(path: string, token?: string): string {
  const base = API_URL.replace("http://", "ws://").replace("https://", "wss://");
  const qs = token ? `?token=${encodeURIComponent(token)}` : "";
  return `${base}${path}${qs}`;
}
