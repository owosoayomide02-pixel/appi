import { HeroCinematic } from "@/components/marketing/HeroCinematic";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Security",
  description: "Guardian, kill switch, folder sandbox, and honest capability reporting.",
};

export default function SecurityPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <HeroCinematic
        title="Guardian sits below the model."
        subtitle="ALLOW, ASK, or BLOCK. Opt-in folders. Secrets as handles. A kill switch that does not ask the AI."
        primaryHref="/register"
        primaryLabel="Get started"
        secondaryHref="/product"
        secondaryLabel="How it works"
      />
      <main className="mx-auto max-w-3xl px-5 py-16 text-slate-300">
        <p className="leading-7">
          Voice never bypasses Guardian. Unsupported abilities return CAPABILITY_UNAVAILABLE. Connectors stay
          disconnected until a verified credential exists.
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
