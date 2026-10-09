/** Browser OS detection for installers (signup / download). */

export type PlatformId = "windows" | "macos" | "linux" | "unknown";

export type PlatformInfo = {
  id: PlatformId;
  label: string;
  kind: "exe" | "macos" | "linux" | "unknown";
  short: string;
};

const LABELS: Record<PlatformId, PlatformInfo> = {
  windows: { id: "windows", label: "Windows", kind: "exe", short: ".exe" },
  macos: { id: "macos", label: "macOS", kind: "macos", short: "Mac" },
  linux: { id: "linux", label: "Linux", kind: "linux", short: "Linux" },
  unknown: { id: "unknown", label: "Your device", kind: "unknown", short: "?" },
};

export function detectPlatform(ua?: string): PlatformInfo {
  const raw = (ua || (typeof navigator !== "undefined" ? navigator.userAgent : "") || "").toLowerCase();
  if (!raw) return LABELS.unknown;
  if (raw.includes("win")) return LABELS.windows;
  if (raw.includes("mac") || raw.includes("iphone") || raw.includes("ipad")) return LABELS.macos;
  if (raw.includes("linux") || raw.includes("android") || raw.includes("cros")) return LABELS.linux;
  return LABELS.unknown;
}

export function platformFromQuery(value: string | null | undefined): PlatformId | null {
  const v = (value || "").toLowerCase().trim();
  if (v === "windows" || v === "win" || v === "exe") return "windows";
  if (v === "macos" || v === "mac" || v === "darwin" || v === "osx") return "macos";
  if (v === "linux") return "linux";
  return null;
}
