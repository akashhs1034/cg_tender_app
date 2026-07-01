'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { AppShell } from '@/components/app-shell'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { useAuth } from '@/lib/auth-context'
import { createClient } from '@/lib/supabase/client'
import { Building2, ShieldCheck, User, Save, LogIn, Loader2, MapPin } from 'lucide-react'

const STATES = ['Chhattisgarh', 'Uttar Pradesh'] as const

interface ProfileForm {
  full_name: string
  company_name: string
  contractor_class: string
  turnover_lakhs: string
  experience_years: string
  states: string[]
  sectors: string
}

const EMPTY: ProfileForm = {
  full_name: '',
  company_name: '',
  contractor_class: '',
  turnover_lakhs: '',
  experience_years: '',
  states: [],
  sectors: '',
}

export default function ProfilePage() {
  const { user, email, loading: authLoading } = useAuth()
  const { toast } = useToast()
  const [form, setForm] = useState<ProfileForm>(EMPTY)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (authLoading) return
    if (!email) {
      setLoading(false)
      return
    }
    let active = true
    const supabase = createClient()
    supabase
      .from('profiles')
      .select('*')
      .eq('email', email)
      .maybeSingle()
      .then(({ data }) => {
        if (!active || !data) return
        setForm({
          full_name: data.full_name ?? '',
          company_name: data.company_name ?? '',
          contractor_class: data.contractor_class ?? '',
          turnover_lakhs: data.turnover_lakhs != null ? String(data.turnover_lakhs) : '',
          experience_years: data.experience_years != null ? String(data.experience_years) : '',
          states: Array.isArray(data.states) ? data.states : [],
          sectors: Array.isArray(data.sectors) ? data.sectors.join(', ') : '',
        })
      })
      .then(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [email, authLoading])

  const set = <K extends keyof ProfileForm>(k: K, v: ProfileForm[K]) =>
    setForm((f) => ({ ...f, [k]: v }))

  const toggleState = (s: string) =>
    setForm((f) => ({
      ...f,
      states: f.states.includes(s) ? f.states.filter((x) => x !== s) : [...f.states, s],
    }))

  const handleSave = async () => {
    if (!email) return
    setSaving(true)
    const supabase = createClient()
    const { error } = await supabase.from('profiles').upsert({
      email,
      full_name: form.full_name || null,
      company_name: form.company_name || null,
      contractor_class: form.contractor_class || null,
      turnover_lakhs: form.turnover_lakhs ? Number(form.turnover_lakhs) : null,
      experience_years: form.experience_years ? Number(form.experience_years) : null,
      states: form.states,
      sectors: form.sectors ? form.sectors.split(',').map((s) => s.trim()).filter(Boolean) : [],
    })
    setSaving(false)
    if (error) toast('Could not save', 'error', { description: error.message })
    else toast('Profile saved', 'success', { description: 'Your matching preferences are updated.' })
  }

  // ── Not signed in ──
  if (!authLoading && !user) {
    return (
      <AppShell pageTitle="Profile" pageSubtitle="Manage your profile and matching preferences">
        <div className="text-center py-20 rounded-2xl border border-border-subtle bg-surface max-w-md mx-auto">
          <User className="w-8 h-8 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary font-medium">Sign in to manage your profile</p>
          <p className="text-sm text-text-muted mt-1">Your profile powers AI matching across tenders and jobs.</p>
          <Link href="/login" className="inline-flex items-center gap-1.5 mt-4 rounded-lg bg-brand-blue px-4 py-2 text-xs font-semibold text-white hover:bg-brand-blue/90 transition-colors">
            <LogIn className="h-3.5 w-3.5" /> Sign In
          </Link>
        </div>
      </AppShell>
    )
  }

  const inputCls =
    'w-full rounded-lg border border-border-subtle bg-surface-elevated px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-brand-blue focus:outline-none transition-colors'

  return (
    <AppShell pageTitle="Profile" pageSubtitle="Manage your profile and matching preferences">
      {loading ? (
        <div className="flex items-center justify-center py-20 text-text-muted">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading your profile…
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <section className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-brand-blue/30 bg-brand-blue/10">
                <User className="h-7 w-7 text-brand-blue" />
              </div>
              <div className="min-w-0">
                <p className="font-heading text-2xl font-bold text-text-primary truncate">{form.full_name || 'Your profile'}</p>
                <p className="mt-1 text-sm text-text-secondary truncate">{email}</p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Full name</span>
                <input className={inputCls} value={form.full_name} onChange={(e) => set('full_name', e.target.value)} placeholder="Your name" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Company name</span>
                <input className={inputCls} value={form.company_name} onChange={(e) => set('company_name', e.target.value)} placeholder="Company / firm" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Contractor class</span>
                <input className={inputCls} value={form.contractor_class} onChange={(e) => set('contractor_class', e.target.value)} placeholder="e.g. Class A" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Annual turnover (₹ lakhs)</span>
                <input type="number" className={inputCls} value={form.turnover_lakhs} onChange={(e) => set('turnover_lakhs', e.target.value)} placeholder="e.g. 250" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Experience (years)</span>
                <input type="number" className={inputCls} value={form.experience_years} onChange={(e) => set('experience_years', e.target.value)} placeholder="e.g. 8" />
              </label>
              <label className="block sm:col-span-2">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Sectors of interest</span>
                <input className={inputCls} value={form.sectors} onChange={(e) => set('sectors', e.target.value)} placeholder="Civil Works, Electrical, IT (comma-separated)" />
              </label>
            </div>

            <div className="mt-5">
              <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-text-muted">States of interest</span>
              <div className="flex flex-wrap gap-2">
                {STATES.map((s) => {
                  const active = form.states.includes(s)
                  return (
                    <button key={s} type="button" onClick={() => toggleState(s)}
                      className={active
                        ? 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-brand-blue/40 bg-brand-blue/10 text-brand-blue'
                        : 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-border-subtle bg-surface-elevated text-text-secondary hover:text-text-primary'}>
                      <MapPin className="w-3.5 h-3.5" /> {s}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <Button onClick={handleSave} disabled={saving} className="bg-brand-blue text-white hover:bg-brand-blue/90 gap-1.5">
                {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                {saving ? 'Saving…' : 'Save Profile'}
              </Button>
            </div>
          </section>

          <aside className="rounded-2xl border border-border-subtle bg-surface p-6 h-fit">
            <p className="font-heading text-lg font-bold text-text-primary">Why this matters</p>
            <p className="mt-2 text-sm leading-relaxed text-text-secondary">
              Your profile drives AI match scores. Turnover and contractor class filter tenders you&apos;re eligible for; sectors and states focus your recommendations.
            </p>
            <div className="mt-5 space-y-3">
              {[
                { icon: Building2, label: 'Eligibility from turnover & class' },
                { icon: ShieldCheck, label: 'Region-focused recommendations' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3 rounded-xl border border-border-subtle bg-background/40 px-4 py-3">
                  <item.icon className="w-4 h-4 text-brand-blue flex-shrink-0" />
                  <span className="text-sm text-text-secondary">{item.label}</span>
                </div>
              ))}
            </div>
          </aside>
        </div>
      )}
    </AppShell>
  )
}
