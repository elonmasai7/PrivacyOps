import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
      <Link href="/" className="text-xl font-bold" style={{ fontFamily: "var(--font-headline)" }}>
        PrivacyOps Africa
      </Link>
      <nav className="flex items-center gap-4 text-sm text-slate-700">
        <Link href="/pricing">Pricing</Link>
        <Link href="/login">Login</Link>
        <Link href="/register" className="rounded-md bg-baobab-700 px-4 py-2 text-white">
          Start Free Scan
        </Link>
      </nav>
    </header>
  );
}
