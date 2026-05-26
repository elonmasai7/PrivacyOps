"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiFetch, setToken } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", full_name: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify(form),
      });
      const token = await apiFetch<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: form.email, password: form.password }),
      });
      setToken(token.access_token);
      router.push("/onboarding");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-6">
      <form className="panel w-full p-6" onSubmit={onSubmit}>
        <h1 className="text-2xl font-bold" style={{ fontFamily: "var(--font-headline)" }}>
          Create your account
        </h1>
        <p className="mt-1 text-sm text-slate-600">Start with real credentials. No demo users are preloaded.</p>
        <label className="mt-4 block text-sm">Full name</label>
        <input className="mt-1 w-full rounded-md border p-2" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        <label className="mt-3 block text-sm">Email</label>
        <input type="email" className="mt-1 w-full rounded-md border p-2" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <label className="mt-3 block text-sm">Password</label>
        <input type="password" className="mt-1 w-full rounded-md border p-2" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
        <button disabled={loading} className="mt-5 w-full rounded-md bg-baobab-700 px-4 py-2 text-white disabled:opacity-60">
          {loading ? "Creating..." : "Register"}
        </button>
        <p className="mt-4 text-sm text-slate-600">
          Already registered? <Link className="text-baobab-700" href="/login">Login</Link>
        </p>
      </form>
    </main>
  );
}
