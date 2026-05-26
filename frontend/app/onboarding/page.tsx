"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

type Organization = {
  id: string;
  name: string;
  slug: string;
  onboarding_completed: boolean;
};

export default function OnboardingPage() {
  const router = useRouter();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const [orgForm, setOrgForm] = useState({
    name: "",
    slug: "",
    country: "Kenya",
    industry: "",
    employee_band: "",
    revenue_band: "",
  });

  const [answers, setAnswers] = useState({
    handles_personal_data: true,
    handles_sensitive_data: false,
    serves_eu_users: false,
    processes_childrens_data: false,
    uses_cloud_services: true,
    uses_third_party_vendors: true,
    has_privacy_policy: false,
    has_dpo: false,
    has_security_policies: false,
    has_incident_response: false,
    soc2_or_iso_required: false,
  });

  async function loadOrgs() {
    try {
      const rows = await apiFetch<Organization[]>("/organizations");
      setOrganizations(rows);
      if (rows.length > 0 && !selectedOrg) {
        setSelectedOrg(rows[0].id);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    loadOrgs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createOrg(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setInfo(null);
    try {
      const created = await apiFetch<Organization>("/organizations", {
        method: "POST",
        body: JSON.stringify(orgForm),
      });
      setSelectedOrg(created.id);
      setInfo("Organization created. Complete onboarding questionnaire next.");
      await loadOrgs();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function submitOnboarding(event: FormEvent) {
    event.preventDefault();
    if (!selectedOrg) {
      setError("Select or create an organization first.");
      return;
    }
    setError(null);
    setInfo(null);
    try {
      const result = await apiFetch<{ trust_readiness_score: number }>(`/organizations/${selectedOrg}/onboarding`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      setInfo(`Onboarding completed. Trust Readiness Score: ${result.trust_readiness_score}`);
      router.push(`/app/${selectedOrg}/dashboard`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <main className="mx-auto w-full max-w-4xl space-y-6 px-6 py-10">
      <h1 className="text-3xl font-bold" style={{ fontFamily: "var(--font-headline)" }}>
        Workspace onboarding
      </h1>
      <section className="panel p-5">
        <h2 className="text-xl font-semibold">1) Create organization workspace</h2>
        <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={createOrg}>
          <input className="rounded-md border p-2" placeholder="Company name" value={orgForm.name} onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })} required />
          <input className="rounded-md border p-2" placeholder="Slug (acme-kenya)" value={orgForm.slug} onChange={(e) => setOrgForm({ ...orgForm, slug: e.target.value })} required />
          <input className="rounded-md border p-2" placeholder="Country" value={orgForm.country} onChange={(e) => setOrgForm({ ...orgForm, country: e.target.value })} required />
          <input className="rounded-md border p-2" placeholder="Industry" value={orgForm.industry} onChange={(e) => setOrgForm({ ...orgForm, industry: e.target.value })} />
          <input className="rounded-md border p-2" placeholder="Employees range" value={orgForm.employee_band} onChange={(e) => setOrgForm({ ...orgForm, employee_band: e.target.value })} />
          <input className="rounded-md border p-2" placeholder="Revenue range" value={orgForm.revenue_band} onChange={(e) => setOrgForm({ ...orgForm, revenue_band: e.target.value })} />
          <button className="rounded-md bg-baobab-700 px-4 py-2 text-white md:col-span-2">Create workspace</button>
        </form>
      </section>

      <section className="panel p-5">
        <h2 className="text-xl font-semibold">2) Complete onboarding questionnaire</h2>
        <label className="mt-3 block text-sm font-medium">Organization</label>
        <select className="mt-1 w-full rounded-md border p-2" value={selectedOrg} onChange={(e) => setSelectedOrg(e.target.value)}>
          <option value="">Select organization</option>
          {organizations.map((org) => (
            <option key={org.id} value={org.id}>{org.name}</option>
          ))}
        </select>
        <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={submitOnboarding}>
          {Object.entries(answers).map(([key, value]) => (
            <label key={key} className="flex items-center gap-2 rounded-md border p-2 text-sm">
              <input type="checkbox" checked={value} onChange={(e) => setAnswers({ ...answers, [key]: e.target.checked })} />
              <span>{key.replaceAll("_", " ")}</span>
            </label>
          ))}
          <button className="rounded-md bg-slatecoast-800 px-4 py-2 text-white md:col-span-2">Run onboarding score</button>
        </form>
      </section>

      {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {info ? <p className="rounded-md bg-green-50 p-3 text-sm text-green-700">{info}</p> : null}
    </main>
  );
}
