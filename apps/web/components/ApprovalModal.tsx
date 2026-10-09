"use client";

import { ApprovalRequest } from "@/lib/types";
import { api } from "@/lib/api";

export function ApprovalModal({
  request,
  projectName,
  deviceName,
  onDone,
}: {
  request: ApprovalRequest;
  projectName?: string;
  deviceName?: string;
  onDone: () => void;
}) {
  async function decide(decision: "approved_once" | "approved_task" | "approved_similar" | "denied") {
    await api(`/api/v1/permissions/requests/${request.id}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    });
    onDone();
  }

  const meta = request.metadata || {};
  const tool = request.tool || "";
  const payment = tool.includes("payment.execute") || Boolean(meta.amount);
  const social = tool.includes("social.publish") || tool.includes("social.message");
  const high = request.risk === "high" || payment;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="glass cmd-shadow w-full max-w-lg rounded-3xl p-6">
        <div className="text-xs tracking-[0.2em] text-[var(--fg-muted)]">PERMISSION REQUIRED</div>
        <h2 className="mt-2 text-2xl font-semibold">
          {payment
            ? `Appi wants to pay ${meta.currency || "₦"}${meta.amount ?? ""}`
            : social
              ? "Appi wants to post content"
              : "Appi wants permission to"}
        </h2>
        <dl className="mt-5 space-y-3 text-sm">
          <div>
            <dt className="text-[var(--fg-muted)]">Action</dt>
            <dd className="font-medium">{request.action}</dd>
          </div>
          {request.command && (
            <div>
              <dt className="text-[var(--fg-muted)]">Command</dt>
              <dd className="font-mono text-xs">{request.command}</dd>
            </div>
          )}
          {Boolean(meta.account) && (
            <div>
              <dt className="text-[var(--fg-muted)]">Account</dt>
              <dd>{String(meta.account)}</dd>
            </div>
          )}
          {Boolean(meta.content) && (
            <div>
              <dt className="text-[var(--fg-muted)]">Content</dt>
              <dd className="whitespace-pre-wrap">{String(meta.content)}</dd>
            </div>
          )}
          {Boolean(meta.visibility) && (
            <div>
              <dt className="text-[var(--fg-muted)]">Visibility</dt>
              <dd>{String(meta.visibility)}</dd>
            </div>
          )}
          {Boolean(meta.merchant) && (
            <div>
              <dt className="text-[var(--fg-muted)]">Merchant</dt>
              <dd>{String(meta.merchant)}</dd>
            </div>
          )}
          {projectName && (
            <div>
              <dt className="text-[var(--fg-muted)]">Project</dt>
              <dd>{projectName}</dd>
            </div>
          )}
          {(deviceName || Boolean(meta.platform)) && (
            <div>
              <dt className="text-[var(--fg-muted)]">Device</dt>
              <dd>{deviceName || String(meta.platform)}</dd>
            </div>
          )}
          <div>
            <dt className="text-[var(--fg-muted)]">Risk</dt>
            <dd className={high ? "text-[var(--danger)]" : "text-[var(--warn)]"}>{request.risk.toUpperCase()}</dd>
          </div>
          <div>
            <dt className="text-[var(--fg-muted)]">Reason</dt>
            <dd>{request.reason}</dd>
          </div>
        </dl>
        {high && (
          <p className="mt-4 rounded-2xl border border-[var(--danger)]/40 bg-[var(--danger)]/10 p-3 text-xs">
            {payment
              ? "Financial action. Banking passwords and card numbers are never sent to the model. Provider tokens only."
              : "High-risk action. Publishing, deleting, or sending cannot be undone easily."}
          </p>
        )}
        <div className="mt-6 flex flex-wrap gap-2">
          {payment ? (
            <>
              <button onClick={() => decide("approved_once")} className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm text-white">
                Authenticate & pay
              </button>
              <button onClick={() => decide("denied")} className="rounded-full border border-[var(--danger)] px-4 py-2 text-sm text-[var(--danger)]">
                Cancel
              </button>
            </>
          ) : (
            <>
              <button onClick={() => decide("approved_once")} className="rounded-full bg-[var(--accent)] px-4 py-2 text-sm text-white">
                Approve once
              </button>
              <button onClick={() => decide("approved_task")} className="rounded-full border border-[var(--line)] px-4 py-2 text-sm">
                Approve for this task
              </button>
              <button onClick={() => decide("approved_similar")} className="rounded-full border border-[var(--line)] px-4 py-2 text-sm">
                Approve similar actions
              </button>
              <button onClick={() => decide("denied")} className="rounded-full border border-[var(--danger)] px-4 py-2 text-sm text-[var(--danger)]">
                Deny
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
