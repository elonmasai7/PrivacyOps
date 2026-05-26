import type { Metadata } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";

import "./globals.css";

const headline = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-headline",
});

const body = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "PrivacyOps Africa",
  description: "Africa-first privacy, compliance, and security posture automation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${headline.variable} ${body.variable}`}>
      <body style={{ fontFamily: "var(--font-body)" }}>{children}</body>
    </html>
  );
}
