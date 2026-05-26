import { SiteHeader } from "@/components/site-header";

const plans = [
  {
    name: "Free Scan",
    tagline: "One workspace, baseline score",
    points: ["1 organization", "Onboarding + basic readiness", "No advanced exports"],
  },
  {
    name: "Starter",
    tagline: "Kenya DPA + GDPR workflows",
    points: ["Manual evidence vault", "Limited users", "Basic report engine"],
  },
  {
    name: "Growth",
    tagline: "Automation for scaling teams",
    points: ["Integrations + posture checks", "DPIA + incidents + vendor risk", "Advanced reports"],
  },
  {
    name: "Enterprise",
    tagline: "Audit-focused operating model",
    points: ["SOC 2 + ISO 27001 readiness", "Trust center + auditor access", "SSO and priority support"],
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto w-full max-w-6xl px-6 pb-16 pt-10">
        <h1 className="text-4xl font-bold" style={{ fontFamily: "var(--font-headline)" }}>
          Pricing built for African growth stages
        </h1>
        <p className="mt-3 text-slate-700">Billing uses a real payment provider when configured. No fake subscription states are shown.</p>
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {plans.map((plan) => (
            <article key={plan.name} className="panel p-5">
              <h2 className="text-xl font-semibold">{plan.name}</h2>
              <p className="mt-1 text-sm text-slate-600">{plan.tagline}</p>
              <ul className="mt-4 space-y-2 text-sm text-slate-700">
                {plan.points.map((point) => (
                  <li key={point}>- {point}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}
