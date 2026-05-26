import Link from "next/link";

import { SiteHeader } from "@/components/site-header";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto grid w-full max-w-6xl gap-10 px-6 pb-16 pt-10 lg:grid-cols-[1.1fr_0.9fr]">
        <section>
          <p className="inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            Africa Compliance Lens
          </p>
          <h1 className="mt-5 text-5xl font-bold leading-tight text-slate-900" style={{ fontFamily: "var(--font-headline)" }}>
            Prove privacy and security readiness for Kenya, the EU, and global audits.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-700">
            PrivacyOps Africa helps startups and enterprises track compliance evidence, automate security posture checks,
            and build trust packs for customers and auditors.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/register" className="rounded-md bg-baobab-700 px-5 py-3 font-semibold text-white">
              Create Workspace
            </Link>
            <Link href="/pricing" className="rounded-md border border-slate-300 px-5 py-3 font-semibold text-slate-800">
              Explore Plans
            </Link>
          </div>
        </section>
        <section className="panel p-6">
          <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-headline)" }}>
            What You Can Run
          </h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-700">
            <li>- Kenya DPA readiness checks and ODPC registration preparation workflow</li>
            <li>- GDPR RoPA, lawful basis tracking, and data subject request management</li>
            <li>- SOC 2 and ISO 27001 readiness evidence collection and gap reporting</li>
            <li>- GitHub-powered security posture findings from real repositories</li>
            <li>- Trust Center with approved documents and customer audit requests</li>
          </ul>
        </section>
      </main>
    </div>
  );
}
