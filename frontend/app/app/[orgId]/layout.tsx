import { AppShell } from "@/components/app-shell";

export default function OrgLayout({ children, params }: { children: React.ReactNode; params: { orgId: string } }) {
  return <AppShell orgId={params.orgId}>{children}</AppShell>;
}
