"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { apiFetch } from "@/lib/api";

type Organization = { id: string; name: string };

export default function AppEntryPage() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Organization[]>("/organizations")
      .then(setOrgs)
      .catch((err) => setError((err as Error).message));
  }, []);

  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl px-6 py-10">
      <h1 className="text-3xl font-bold" style={{ fontFamily: "var(--font-headline)" }}>
        Choose workspace
      </h1>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      {orgs.length === 0 ? (
        <div className="empty-state mt-5">
          <p className="text-sm">No organizations found. Create one in onboarding.</p>
          <Link className="mt-3 inline-block rounded-md bg-baobab-700 px-4 py-2 text-sm text-white" href="/onboarding">
            Go to onboarding
          </Link>
        </div>
      ) : (
        <div className="mt-5 grid gap-3">
          {orgs.map((org) => (
            <Link key={org.id} className="panel p-4 hover:border-baobab-500" href={`/app/${org.id}/dashboard`}>
              <p className="font-semibold">{org.name}</p>
              <p className="text-sm text-slate-600">Open workspace</p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
