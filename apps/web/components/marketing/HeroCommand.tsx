"use client";

import { ArrowUpRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function HeroCommand() {
  const router = useRouter();
  const [value, setValue] = useState("");

  function go() {
    const q = value.trim();
    router.push(q ? `/register?intent=${encodeURIComponent(q)}` : "/register");
  }

  return (
    <div className="glass cmd-shadow mx-auto mt-10 max-w-3xl rounded-[1.8rem] p-3">
      <label className="sr-only" htmlFor="appi-hero-command">
        Tell Appi what you need done
      </label>
      <div className="flex items-end gap-3">
        <textarea
          id="appi-hero-command"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              go();
            }
          }}
          placeholder="Open the project, find why npm run dev is failing, fix it, run the tests and tell me what you changed."
          className="min-h-28 flex-1 resize-none bg-transparent p-4 text-base outline-none"
        />
        <button
          onClick={go}
          className="mb-1 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--accent)] text-white"
          aria-label="Continue with this task"
        >
          <ArrowUpRight size={18} />
        </button>
      </div>
    </div>
  );
}
