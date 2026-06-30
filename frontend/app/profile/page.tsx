'use client'

import { useState } from 'react'
import { AppShell } from '@/components/app-shell'
import { Button } from '@/components/ui/button'
import { Modal } from '@/components/ui/modal'
import { useToast } from '@/components/ui/toast'
import { Building2, Bell, FileText, ShieldCheck, User, Pencil } from 'lucide-react'

const profileItems = [
  { label: 'Role', value: 'Contractor / Business', icon: Building2 },
  { label: 'Primary region', value: 'CG & UP', icon: ShieldCheck },
  { label: 'Saved categories', value: 'Construction, Supply, IT Services', icon: FileText },
  { label: 'Alerts', value: 'Email + WhatsApp ready', icon: Bell },
]

const editFields = [
  { label: 'Full name', value: 'Rajesh Kumar' },
  { label: 'Role', value: 'Contractor / Business' },
  { label: 'Primary region', value: 'CG & UP' },
  { label: 'Saved categories', value: 'Construction, Supply, IT Services' },
]

export default function ProfilePage() {
  const [editOpen, setEditOpen] = useState(false)
  const { toast } = useToast()

  const handleSave = () => {
    setEditOpen(false)
    toast('Profile saved', 'success', { description: 'Demo only — changes persist after backend integration.' })
  }

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
            <Button onClick={() => setEditOpen(true)} className="bg-brand-blue text-white hover:bg-brand-blue/90 gap-1.5">
              <Pencil className="h-3.5 w-3.5" /> Edit Profile
            </Button>
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

      {/* Mock edit modal */}
      <Modal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        eyebrow="Profile"
        title="Edit Profile"
        icon={<Pencil className="h-4 w-4" />}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setEditOpen(false)} className="text-xs h-8">Cancel</Button>
            <Button size="sm" onClick={handleSave} className="bg-brand-blue hover:bg-brand-blue/90 text-white text-xs h-8">Save changes</Button>
          </>
        }
      >
        <div className="space-y-4">
          {editFields.map((f) => (
            <label key={f.label} className="block">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">{f.label}</span>
              <input
                defaultValue={f.value}
                className="w-full rounded-lg border border-border-subtle bg-surface-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-brand-blue focus:outline-none"
              />
            </label>
          ))}
          <p className="text-[10px] text-text-muted">Demo form — values reset on close until your account is connected to the backend.</p>
        </div>
      </Modal>
    </AppShell>
  )
}
