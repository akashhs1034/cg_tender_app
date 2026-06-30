import { AppShell } from '@/components/app-shell'
import { Button } from '@/components/ui/button'
import { Building2, Bell, FileText, ShieldCheck, User } from 'lucide-react'

const profileItems = [
  { label: 'Role', value: 'Contractor / Business', icon: Building2 },
  { label: 'Primary region', value: 'CG & UP', icon: ShieldCheck },
  { label: 'Saved categories', value: 'Construction, Supply, IT Services', icon: FileText },
  { label: 'Alerts', value: 'Email + WhatsApp ready', icon: Bell },
]

export default function ProfilePage() {
  return (
    <AppShell pageTitle="Profile" pageSubtitle="Manage your OPPORTA profile and matching preferences">
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <section className="rounded-2xl border border-border-subtle bg-surface p-6">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-brand-blue/30 bg-brand-blue/10">
                <User className="h-7 w-7 text-brand-blue" />
              </div>
              <div>
                <p className="font-heading text-2xl font-bold text-text-primary">Rajesh Kumar</p>
                <p className="mt-1 text-sm text-text-secondary">Contractor profile · Placeholder account</p>
              </div>
            </div>
            <Button className="bg-brand-blue text-white hover:bg-brand-blue/90">Edit Profile</Button>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {profileItems.map((item) => (
              <div key={item.label} className="rounded-xl border border-border-subtle bg-surface-elevated/60 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-blue/10">
                    <item.icon className="h-4 w-4 text-brand-blue" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{item.label}</p>
                    <p className="mt-0.5 text-sm font-semibold text-text-primary">{item.value}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <aside className="rounded-2xl border border-border-subtle bg-surface p-6">
          <p className="font-heading text-lg font-bold text-text-primary">Matching preferences</p>
          <p className="mt-2 text-sm leading-relaxed text-text-secondary">
            These placeholder preferences will later connect to your real profile, company documents, job resume, and alert settings.
          </p>
          <div className="mt-5 space-y-3">
            {['State and district focus', 'Tender categories', 'Job categories', 'Deadline alerts'].map((item) => (
              <div key={item} className="flex items-center justify-between rounded-xl border border-border-subtle bg-background/40 px-4 py-3">
                <span className="text-sm text-text-secondary">{item}</span>
                <span className="text-xs font-semibold text-success">Ready</span>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </AppShell>
  )
}
