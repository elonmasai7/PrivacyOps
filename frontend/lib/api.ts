export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem("privacyops_token");
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem("privacyops_token", token);
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(init?.headers ?? {}),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function apiFetchForm<T>(path: string, form: FormData): Promise<T> {
  const headers: HeadersInit = {};
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with ${res.status}`);
  }
  return res.json() as Promise<T>;
}
