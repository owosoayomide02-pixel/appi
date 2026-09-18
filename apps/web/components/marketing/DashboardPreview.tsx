export function DashboardPreview() {
  const steps = [
    { n: "01", title: "Inspect package.json", tool: "files.read", status: "succeeded" },
    { n: "02", title: "Capture npm run dev error", tool: "terminal.run_command", status: "succeeded" },
    { n: "03", title: "Apply the missing dependency fix", tool: "files.write", status: "verifying" },
    { n: "04", title: "Run tests and health-check the server", tool: "project.run_tests", status: "pending" },
  ];

  return (
    <div className="glass cmd-shadow overflow-hidden rounded-[2rem]">
      <div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-3 text-xs text-[var(--fg-muted)]">
        <span className="tracking-[0.2em]">OPERATOR</span>
        <span className="rounded-full border border-[var(--danger)] px-3 py-1 uppercase tracking-[0.14em] text-[var(--danger)]">
          Stop Appi
        </span>
      </div>
      <div className="grid md:grid-cols-[200px_1fr]">
        <aside className="hidden border-r border-[var(--line)] p-5 text-sm text-[var(--fg-muted)] md:block">
          <div className="font-[family-name:var(--font-display)] text-lg tracking-[0.16em] text-[var(--fg)]">APPI</div>
          <div className="mt-1 text-xs">Think. Act. Verify.</div>
          <ul className="mt-6 space-y-2">
            <li className="text-[var(--accent)]">New Task</li>
            <li>Active Tasks</li>
            <li>Devices</li>
            <li>Activity Log</li>
          </ul>
        </aside>
        <div className="p-5">
          <div className="text-xs tracking-[0.2em] text-[var(--fg-muted)]">GOAL</div>
          <h3 className="mt-1 text-xl">Fix development server failure</h3>
          <ol className="mt-5 space-y-2">
            {steps.map((step) => (
              <li key={step.n} className="flex items-center justify-between rounded-2xl border border-[var(--line)] px-4 py-3 text-sm">
                <div>
                  <span className="mr-3 font-mono text-xs text-[var(--fg-muted)]">{step.n}</span>
                  {step.title}
                  <div className="ml-8 font-mono text-[11px] text-[var(--fg-muted)]">{step.tool}</div>
                </div>
                <span className={step.status === "succeeded" ? "text-[var(--ok)]" : step.status === "verifying" ? "text-[var(--accent)]" : "text-[var(--fg-muted)]"}>
                  {step.status}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
