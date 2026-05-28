"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const moduleLinks = [
  ["Dashboard", "dashboard"],
  ["Frameworks", "frameworks"],
  ["Kenya DPA", "kenya-dpa"],
  ["GDPR", "gdpr"],
  ["SOC 2", "soc2"],
  ["ISO 27001", "iso27001"],
  ["Data Inventory", "data-inventory"],
  ["DPIA", "dpia"],
  ["Data Subject Requests", "dsr"],
  ["Incidents", "incidents"],
  ["Vendors", "vendors"],
  ["Evidence Vault", "evidence"],
  ["Policies", "policies"],
  ["Reports", "reports"],
  ["Security Posture", "security-posture"],
  ["Integrations", "integrations"],
  ["Tasks", "tasks"],
  ["Trust Center", "trust-center"],
  ["Billing", "billing"],
  ["Audit Logs", "audit-logs"],
  ["Settings", "settings"],
  ["Admin Panel", "admin"],
];

export function AppShell({ orgId, children }: { orgId: string; children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slatecoast-900 text-slate-100">
      <div className="mx-auto grid min-h-screen max-w-[1400px] grid-cols-1 lg:grid-cols-[280px_1fr]">
        <aside className="border-r border-slate-700 bg-slatecoast-800 p-5">
          <p className="text-lg font-semibold" style={{ fontFamily: "var(--font-headline)" }}>
            PrivacyOps Africa
          </p>
          <p className="mt-1 text-xs text-slate-300">Org: {orgId}</p>
          <nav className="mt-6 flex max-h-[78vh] flex-col gap-1 overflow-auto">
            {moduleLinks.map(([label, slug]) => {
              const href = `/app/${orgId}/${slug}`;
              const active = pathname === href;
              return (
                <Link
                  key={slug}
                  href={href}
                  className={`rounded-md px-3 py-2 text-sm transition ${active ? "bg-baobab-700 text-white" : "text-slate-300 hover:bg-slatecoast-700"}`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="bg-slate-50 p-6 text-slate-900">{children}</main>
      </div>
    </div>
  );
}
