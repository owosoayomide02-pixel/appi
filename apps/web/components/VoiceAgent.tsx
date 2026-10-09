"use client";

import { useCallback, useState } from "react";
import { Mic, MicOff, X } from "lucide-react";
import {
  LiveKitRoom,
  BarVisualizer,
  useVoiceAssistant,
  VoiceAssistantControlBar,
  RoomAudioRenderer,
  DisconnectButton,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { api } from "@/lib/api";

// ─── Inner component (rendered once we're inside the LiveKitRoom) ─────────────
function VoiceAgentUI({ onClose }: { onClose: () => void }) {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      {/* Animated audio wave — shows Appi "speaking" or "listening" */}
      <div className="w-full h-24">
        <BarVisualizer
          state={state}
          barCount={20}
          trackRef={audioTrack}
          className="w-full h-full"
          options={{ minHeight: 6 }}
        />
      </div>

      <p className="text-xs text-[var(--fg-muted)] capitalize tracking-widest">
        {state === "listening" && "Appi is listening…"}
        {state === "thinking" && "Appi is thinking…"}
        {state === "speaking" && "Appi is speaking…"}
        {state === "idle" && "Say something…"}
        {state === "connecting" && "Connecting…"}
      </p>

      {/* Mute / unmute and disconnect controls */}
      <div className="flex items-center gap-3">
        <VoiceAssistantControlBar />
        <DisconnectButton onClick={onClose}>
          <button
            className="flex items-center gap-1 rounded-full border border-[var(--danger)] px-3 py-1.5 text-xs text-[var(--danger)] hover:bg-[var(--danger)]/10"
          >
            <X size={12} /> End
          </button>
        </DisconnectButton>
      </div>

      {/* Plays Appi's voice through your speakers */}
      <RoomAudioRenderer />
    </div>
  );
}

// ─── Main floating button / panel ────────────────────────────────────────────
export function VoiceAgent() {
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [livekitUrl, setLivekitUrl] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api<{ token: string; livekit_url: string }>(
        "/api/v1/voice/token"
      );
      const url =
        data.livekit_url ||
        process.env.NEXT_PUBLIC_LIVEKIT_URL ||
        "wss://appi-f84mprub.livekit.cloud";
      setToken(data.token);
      setLivekitUrl(url);
      setOpen(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect");
    } finally {
      setLoading(false);
    }
  }, []);

  const endSession = useCallback(() => {
    setOpen(false);
    setToken(null);
  }, []);

  return (
    <>
      {/* ── Floating mic button (always visible in dashboard) ── */}
      {!open && (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
          {error && (
            <p className="rounded-xl bg-[var(--danger)]/10 border border-[var(--danger)] px-3 py-1.5 text-xs text-[var(--danger)]">
              {error}
            </p>
          )}
          <button
            onClick={startSession}
            disabled={loading}
            className="flex items-center gap-2 rounded-full bg-[var(--brand,#6366f1)] px-5 py-3 text-sm font-medium text-white shadow-lg transition hover:scale-105 disabled:opacity-60"
            title="Talk to Appi"
          >
            {loading ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Mic size={18} />
            )}
            {loading ? "Connecting…" : "Talk to Appi"}
          </button>
        </div>
      )}

      {/* ── Voice panel (shown once connected) ── */}
      {open && token && (
        <div className="fixed bottom-6 right-6 z-50 w-80">
          <div className="glass rounded-3xl border border-[var(--line)] p-5 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-semibold tracking-wide">
                Appi Voice
              </span>
              <button
                onClick={endSession}
                className="rounded-full p-1 hover:bg-white/10"
                aria-label="Close voice panel"
              >
                <MicOff size={14} />
              </button>
            </div>

            {/* LiveKitRoom wraps everything that needs WebRTC */}
            <LiveKitRoom
              serverUrl={livekitUrl}
              token={token}
              connect={true}
              audio={true}
              video={false}
              onDisconnected={endSession}
            >
              <VoiceAgentUI onClose={endSession} />
            </LiveKitRoom>
          </div>
        </div>
      )}
    </>
  );
}
