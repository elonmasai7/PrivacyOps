"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ModulePage } from "@/components/module-page";
import { API_BASE, apiFetch, apiFetchForm, getToken } from "@/lib/api";
import { moduleMeta } from "@/lib/modules";

type Props = {
  params: {
    orgId: string;
    module: string;
  };
};

type ProcessingActivity = {
  id: string;
  name: string;
  lawful_basis: string;
  risk_level: string;
  created_at: string;
};

type Evidence = {
  id: string;
  title: string;
  source: string;
  collection_method: string;
  approval_status: string;
};

type Report = {
  id: string;
  framework: string;
  report_type: string;
  score: number;
  created_at: string;
};

type Integration = {
  id: string;
  provider: string;
  status: string;
  last_synced_at: string | null;
  last_error: string | null;
};

type Finding = {
  id: string;
  title: string;
  severity: string;
  category: string;
  status: string;
};

type DashboardData = {
  organization: { name: string; trust_readiness_score: number };
  framework_scores: Record<string, number>;
  risk_heatline: { open_findings: number; open_incidents: number; missing_evidence: number };
};

function DashboardPanel({ orgId }: { orgId: string }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [readiness, setReadiness] = useState<{ computed_readiness_score: number; control_confidence_level: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<DashboardData>(`/dashboard/${orgId}`)
      .then(setData)
      .catch((err) => setError((err as Error).message));
    apiFetch<{ computed_readiness_score: number; control_confidence_level: string }>(`/readiness/${orgId}`)
      .then(setReadiness)
      .catch(() => undefined);
  }, [orgId]);

  if (error) {
    return <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>;
  }

  if (!data) {
    return <p className="text-sm text-slate-600">Loading dashboard...</p>;
  }

  return (
    <section className="grid gap-3 md:grid-cols-4">
      <article className="panel p-4">
        <p className="text-xs text-slate-500">Trust Readiness Score</p>
        <p className="mt-1 text-3xl font-bold text-baobab-700">{data.organization.trust_readiness_score}</p>
      </article>
      <article className="panel p-4">
        <p className="text-xs text-slate-500">Computed Readiness</p>
        <p className="mt-1 text-3xl font-bold text-slatecoast-800">{readiness?.computed_readiness_score ?? "-"}</p>
      </article>
      <article className="panel p-4">
        <p className="text-xs text-slate-500">Open Findings</p>
        <p className="mt-1 text-3xl font-bold text-savanna-700">{data.risk_heatline.open_findings}</p>
      </article>
      <article className="panel p-4">
        <p className="text-xs text-slate-500">Confidence Level</p>
        <p className="mt-1 text-lg font-semibold">{readiness?.control_confidence_level ?? "pending"}</p>
      </article>
    </section>
  );
}

function ProcessingActivityPanel({ orgId }: { orgId: string }) {
  const [items, setItems] = useState<ProcessingActivity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    data_categories: "",
    data_subject_categories: "",
    purpose: "",
    lawful_basis: "consent",
    system_name: "",
    data_location: "",
    vendor_name: "",
    retention_period: "",
    security_measures: "",
    cross_border_transfer: false,
    risk_level: "medium",
  });

  const load = () =>
    apiFetch<ProcessingActivity[]>(`/processing-activities/${orgId}`)
      .then(setItems)
      .catch((err) => setError((err as Error).message));

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await apiFetch(`/processing-activities/${orgId}`, {
        method: "POST",
        body: JSON.stringify({
          ...form,
          data_categories: form.data_categories.split(",").map((v) => v.trim()).filter(Boolean),
          data_subject_categories: form.data_subject_categories.split(",").map((v) => v.trim()).filter(Boolean),
        }),
      });
      setForm({
        ...form,
        name: "",
        data_categories: "",
        data_subject_categories: "",
        purpose: "",
        system_name: "",
        data_location: "",
        vendor_name: "",
        retention_period: "",
        security_measures: "",
      });
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <section className="panel p-5">
      <h2 className="text-lg font-semibold">Create processing activity</h2>
      <form className="mt-3 grid gap-2 md:grid-cols-2" onSubmit={submit}>
        <input className="rounded-md border p-2" placeholder="Activity name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Lawful basis" value={form.lawful_basis} onChange={(e) => setForm({ ...form, lawful_basis: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Data categories (comma separated)" value={form.data_categories} onChange={(e) => setForm({ ...form, data_categories: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Data subject categories" value={form.data_subject_categories} onChange={(e) => setForm({ ...form, data_subject_categories: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="System / application" value={form.system_name} onChange={(e) => setForm({ ...form, system_name: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Data location" value={form.data_location} onChange={(e) => setForm({ ...form, data_location: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Retention period" value={form.retention_period} onChange={(e) => setForm({ ...form, retention_period: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Risk level" value={form.risk_level} onChange={(e) => setForm({ ...form, risk_level: e.target.value })} required />
        <textarea className="rounded-md border p-2 md:col-span-2" placeholder="Purpose of processing" value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} required />
        <textarea className="rounded-md border p-2 md:col-span-2" placeholder="Security measures" value={form.security_measures} onChange={(e) => setForm({ ...form, security_measures: e.target.value })} required />
        <label className="flex items-center gap-2 text-sm md:col-span-2">
          <input type="checkbox" checked={form.cross_border_transfer} onChange={(e) => setForm({ ...form, cross_border_transfer: e.target.checked })} />
          Cross-border transfer involved
        </label>
        <button className="rounded-md bg-baobab-700 px-4 py-2 text-white md:col-span-2">Save activity</button>
      </form>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      <div className="mt-4 space-y-2">
        {items.map((item) => (
          <div key={item.id} className="rounded-md border p-3">
            <p className="font-medium">{item.name}</p>
            <p className="text-sm text-slate-600">Lawful basis: {item.lawful_basis} | Risk: {item.risk_level}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function EvidencePanel({ orgId }: { orgId: string }) {
  const [items, setItems] = useState<Evidence[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", source: "upload", collection_method: "manual" });
  const [file, setFile] = useState<File | null>(null);

  const load = () =>
    apiFetch<Evidence[]>(`/evidence/${orgId}`)
      .then(setItems)
      .catch((err) => setError((err as Error).message));

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Select a file before upload.");
      return;
    }
    const data = new FormData();
    data.append("title", form.title);
    data.append("source", form.source);
    data.append("collection_method", form.collection_method);
    data.append("file", file);

    try {
      await apiFetchForm(`/evidence/${orgId}/upload`, data);
      setForm({ title: "", source: "upload", collection_method: "manual" });
      setFile(null);
      load();
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <section className="panel p-5">
      <h2 className="text-lg font-semibold">Upload evidence</h2>
      <form className="mt-3 grid gap-2 md:grid-cols-2" onSubmit={submit}>
        <input className="rounded-md border p-2" placeholder="Evidence title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Source" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Collection method" value={form.collection_method} onChange={(e) => setForm({ ...form, collection_method: e.target.value })} required />
        <input className="rounded-md border p-2" type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} required />
        <button className="rounded-md bg-baobab-700 px-4 py-2 text-white md:col-span-2">Upload</button>
      </form>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      <div className="mt-4 space-y-2">
        {items.map((item) => (
          <div key={item.id} className="rounded-md border p-3">
            <p className="font-medium">{item.title}</p>
            <p className="text-sm text-slate-600">
              {item.source} via {item.collection_method} | Approval: {item.approval_status}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ReportsPanel({ orgId }: { orgId: string }) {
  const [items, setItems] = useState<Report[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ report_type: "board_summary", framework: "Kenya Data Protection Act" });

  const load = () =>
    apiFetch<Report[]>(`/reports/${orgId}`)
      .then(setItems)
      .catch((err) => setError((err as Error).message));

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await apiFetch(`/reports/${orgId}`, { method: "POST", body: JSON.stringify(form) });
      load();
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const formats = useMemo(() => ["pdf", "docx", "csv", "json"], []);

  async function download(reportId: string, format: string) {
    const token = getToken();
    const response = await fetch(`${API_BASE}/reports/${orgId}/${reportId}/export/${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      setError(`Could not download ${format.toUpperCase()} export`);
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${reportId}.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="panel p-5">
      <h2 className="text-lg font-semibold">Generate reports</h2>
      <form className="mt-3 grid gap-2 md:grid-cols-2" onSubmit={submit}>
        <input className="rounded-md border p-2" placeholder="Report type" value={form.report_type} onChange={(e) => setForm({ ...form, report_type: e.target.value })} required />
        <input className="rounded-md border p-2" placeholder="Framework" value={form.framework} onChange={(e) => setForm({ ...form, framework: e.target.value })} required />
        <button className="rounded-md bg-baobab-700 px-4 py-2 text-white md:col-span-2">Generate</button>
      </form>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      <div className="mt-4 space-y-2">
        {items.map((item) => (
          <div key={item.id} className="rounded-md border p-3">
            <p className="font-medium">{item.framework} - {item.report_type}</p>
            <p className="text-sm text-slate-600">Score: {item.score}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs">
              {formats.map((format) => (
                <button
                  key={format}
                  className="rounded-md border px-2 py-1"
                  type="button"
                  onClick={() => download(item.id, format)}
                >
                  Download {format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function IntegrationsPanel({ orgId }: { orgId: string }) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState("");

  const load = () => {
    apiFetch<Integration[]>(`/integrations/${orgId}`)
      .then(setIntegrations)
      .catch((err) => setError((err as Error).message));
    apiFetch<Finding[]>(`/integrations/${orgId}/findings`)
      .then(setFindings)
      .catch(() => undefined);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  async function connect(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await apiFetch(`/integrations/${orgId}/connect`, {
        method: "POST",
        body: JSON.stringify({ provider: "github", personal_access_token: token }),
      });
      setToken("");
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function syncGithub() {
    setError(null);
    try {
      await apiFetch(`/integrations/${orgId}/github/sync`, { method: "POST" });
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <section className="space-y-4">
      <div className="panel p-5">
        <h2 className="text-lg font-semibold">Connect GitHub</h2>
        <p className="mt-1 text-sm text-slate-600">Use a real personal access token with least privilege repository read permissions.</p>
        <form className="mt-3 flex flex-col gap-2 md:flex-row" onSubmit={connect}>
          <input className="w-full rounded-md border p-2" type="password" placeholder="github_pat_..." value={token} onChange={(e) => setToken(e.target.value)} required />
          <button className="rounded-md bg-baobab-700 px-4 py-2 text-white">Connect</button>
        </form>
        <button className="mt-3 rounded-md border px-4 py-2 text-sm" onClick={syncGithub}>Run GitHub security sync</button>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      </div>

      <div className="panel p-5">
        <h3 className="text-base font-semibold">Integration status</h3>
        {integrations.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">No integrations connected yet.</p>
        ) : (
          <div className="mt-2 space-y-2">
            {integrations.map((item) => (
              <div key={item.id} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{item.provider}</p>
                <p>Status: {item.status}</p>
                <p>Last synced: {item.last_synced_at ?? "never"}</p>
                {item.last_error ? <p className="text-red-700">{item.last_error}</p> : null}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel p-5">
        <h3 className="text-base font-semibold">Security findings</h3>
        {findings.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">No findings yet. Connect and sync GitHub to pull real posture findings.</p>
        ) : (
          <div className="mt-2 space-y-2">
            {findings.map((finding) => (
              <div key={finding.id} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{finding.title}</p>
                <p>Severity: {finding.severity} | Category: {finding.category} | Status: {finding.status}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default function ModuleRoutePage({ params }: Props) {
  const meta = moduleMeta[params.module];

  if (!meta) {
    return (
      <ModulePage
        title="Module not found"
        subtitle="This route does not map to a known workspace module."
        emptyHeading="Check navigation"
        emptyBody="Use the sidebar to open a valid module route."
      />
    );
  }

  return (
    <div className="space-y-6">
      <ModulePage {...meta} />
      {params.module === "dashboard" ? <DashboardPanel orgId={params.orgId} /> : null}
      {params.module === "data-inventory" ? <ProcessingActivityPanel orgId={params.orgId} /> : null}
      {params.module === "evidence" ? <EvidencePanel orgId={params.orgId} /> : null}
      {params.module === "reports" ? <ReportsPanel orgId={params.orgId} /> : null}
      {params.module === "integrations" || params.module === "security-posture" ? (
        <IntegrationsPanel orgId={params.orgId} />
      ) : null}
    </div>
  );
}
