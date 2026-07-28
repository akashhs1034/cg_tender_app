'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { AppShell } from '@/components/app-shell'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { useAuth } from '@/lib/auth-context'
import { createClient } from '@/lib/supabase/client'
import {
  Building2,
  BookOpen,
  ShieldCheck,
  User,
  Save,
  LogIn,
  Loader2,
  MapPin,
  Mail,
  RefreshCw,
} from 'lucide-react'

const STATES = ['Chhattisgarh', 'Uttar Pradesh'] as const

interface ContractorForm {
  full_name: string
  company_name: string
  contractor_class: string
  turnover_lakhs: string
  experience_years: string
  states: string[]
  sectors: string
  email_alerts: boolean
}

interface JobSeekerForm {
  full_name: string
  qualification: string
  degree_type: string
  job_experience_years: string
  job_skills: string
  job_category: string
  languages: string
  states: string[]
  email_alerts: boolean
}

const EMPTY_CONTRACTOR: ContractorForm = {
  full_name: '',
  company_name: '',
  contractor_class: '',
  turnover_lakhs: '',
  experience_years: '',
  states: [],
  sectors: '',
  email_alerts: true,
}

const EMPTY_JOB_SEEKER: JobSeekerForm = {
  full_name: '',
  qualification: '',
  degree_type: '',
  job_experience_years: '',
  job_skills: '',
  job_category: '',
  languages: '',
  states: [],
  email_alerts: true,
}

function toStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : []
}

export default function ProfilePage() {
  const { user, email, role, loading: authLoading } = useAuth()
  const { toast } = useToast()
  const [contractor, setContractor] = useState<ContractorForm>(EMPTY_CONTRACTOR)
  const [jobSeeker, setJobSeeker] = useState<JobSeekerForm>(EMPTY_JOB_SEEKER)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true

    async function loadProfile() {
      if (authLoading) return
      if (!user || !email || !role) {
        if (active) setLoading(false)
        return
      }

      if (role === 'jobseeker') {
        const meta = (user.user_metadata ?? {}) as Record<string, unknown>
        if (!active) return
        setJobSeeker({
          full_name: typeof meta.full_name === 'string' ? meta.full_name : '',
          qualification: typeof meta.qualification === 'string' ? meta.qualification : '',
          degree_type: typeof meta.degree_type === 'string' ? meta.degree_type : '',
          job_experience_years: typeof meta.job_experience_years === 'number' || typeof meta.job_experience_years === 'string' ? String(meta.job_experience_years) : '',
          job_skills: toStringList(meta.job_skills).join(', '),
          job_category: typeof meta.job_category === 'string' ? meta.job_category : '',
          languages: toStringList(meta.languages).join(', '),
          states: toStringList(meta.states_of_interest),
          email_alerts: meta.email_alerts !== false,
        })
        setLoading(false)
        return
      }

      const fallbackFullName =
        typeof user.user_metadata?.full_name === 'string'
          ? user.user_metadata.full_name
          : ''
      const supabase = createClient()
      try {
        const { data } = await supabase
          .from('profiles')
          .select('*')
          .eq('email', email)
          .maybeSingle()

        if (!active) return
        setContractor({
          full_name: data?.full_name ?? fallbackFullName,
          company_name: data?.company_name ?? '',
          contractor_class: data?.contractor_class ?? '',
          turnover_lakhs: data?.turnover_lakhs != null ? String(data.turnover_lakhs) : '',
          experience_years: data?.experience_years != null ? String(data.experience_years) : '',
          states: Array.isArray(data?.states) ? data.states : [],
          sectors: Array.isArray(data?.sectors) ? data.sectors.join(', ') : '',
          email_alerts: data?.email_alerts !== false,
        })
      } finally {
        if (active) setLoading(false)
      }
    }

    void loadProfile()

    return () => {
      active = false
    }
  }, [authLoading, email, role, user])

  const toggleContractorState = (state: string) => {
    setContractor((current) => ({
      ...current,
      states: current.states.includes(state)
        ? current.states.filter((item) => item !== state)
        : [...current.states, state],
    }))
  }

  const toggleJobState = (state: string) => {
    setJobSeeker((current) => ({
      ...current,
      states: current.states.includes(state)
        ? current.states.filter((item) => item !== state)
        : [...current.states, state],
    }))
  }

  const saveContractor = async () => {
    if (!email) return
    setSaving(true)
    const supabase = createClient()
    const { error } = await supabase.from('profiles').upsert({
      email,
      full_name: contractor.full_name || null,
      company_name: contractor.company_name || null,
      contractor_class: contractor.contractor_class || null,
      turnover_lakhs: contractor.turnover_lakhs ? Number(contractor.turnover_lakhs) : null,
      experience_years: contractor.experience_years ? Number(contractor.experience_years) : null,
      states: contractor.states,
      sectors: contractor.sectors.split(',').map((item) => item.trim()).filter(Boolean),
      email_alerts: contractor.email_alerts,
    })
    setSaving(false)
    if (error) toast('Could not save', 'error', { description: error.message })
    else toast('Contractor profile saved', 'success', { description: 'Tender recommendations will use these preferences.' })
  }

  const saveJobSeeker = async () => {
    if (!user) return
    setSaving(true)
    const supabase = createClient()
    const currentMeta = (user.user_metadata ?? {}) as Record<string, unknown>
    const { error } = await supabase.auth.updateUser({
      data: {
        ...currentMeta,
        full_name: jobSeeker.full_name,
        role: 'jobseeker',
        qualification: jobSeeker.qualification,
        degree_type: jobSeeker.degree_type,
        job_experience_years: jobSeeker.job_experience_years ? Number(jobSeeker.job_experience_years) : 0,
        job_skills: jobSeeker.job_skills.split(',').map((item) => item.trim()).filter(Boolean),
        job_category: jobSeeker.job_category,
        languages: jobSeeker.languages.split(',').map((item) => item.trim()).filter(Boolean),
        states_of_interest: jobSeeker.states,
        email_alerts: jobSeeker.email_alerts,
      },
    })
    setSaving(false)
    if (error) toast('Could not save', 'error', { description: error.message })
    else toast('Job seeker profile saved', 'success', { description: 'Your job workspace has been updated.' })
  }

  if (!authLoading && !user) {
    return (
      <AppShell pageTitle="Profile" pageSubtitle="Manage your matching preferences">
        <div className="text-center py-20 rounded-2xl border border-border-subtle bg-surface max-w-md mx-auto">
          <User className="w-8 h-8 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary font-medium">Sign in to manage your profile</p>
          <Link href="/login" className="inline-flex items-center gap-1.5 mt-4 rounded-lg bg-brand-blue px-4 py-2 text-xs font-semibold text-white hover:bg-brand-blue/90 transition-colors">
            <LogIn className="h-3.5 w-3.5" /> Sign In
          </Link>
        </div>
      </AppShell>
    )
  }

  if (!authLoading && user && !role) {
    return (
      <AppShell pageTitle="Choose your experience" pageSubtitle="Select the workspace that matches your goal">
        <div className="text-center py-20 rounded-2xl border border-border-subtle bg-surface max-w-md mx-auto">
          <RefreshCw className="w-8 h-8 text-brand-blue mx-auto mb-3" />
          <p className="text-text-secondary font-medium">Your account needs an experience</p>
          <p className="text-sm text-text-muted mt-1">Choose Contractor or Job Seeker to personalise OPPORTA.</p>
          <Link href="/select-role" className="inline-flex items-center gap-1.5 mt-4 rounded-lg bg-brand-blue px-4 py-2 text-xs font-semibold text-white hover:bg-brand-blue/90 transition-colors">
            Choose Experience
          </Link>
        </div>
      </AppShell>
    )
  }

  const inputClass = 'w-full rounded-lg border border-border-subtle bg-surface-elevated px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-brand-blue focus:outline-none transition-colors'
  const title = role === 'jobseeker' ? 'Job Seeker Profile' : 'Contractor Profile'
  const subtitle = role === 'jobseeker'
    ? 'Qualifications and preferences for your job workspace'
    : 'Business details used for tender matching'

  return (
    <AppShell pageTitle={title} pageSubtitle={subtitle} bg={role === 'jobseeker' ? 'jobs' : 'tenders'}>
      {loading ? (
        <div className="flex items-center justify-center py-20 text-text-muted">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading your profile…
        </div>
      ) : role === 'jobseeker' ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <section className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-[#6C3EF4]/30 bg-[#6C3EF4]/10">
                <BookOpen className="h-6 w-6 text-[#6C3EF4]" />
              </div>
              <div>
                <h2 className="font-heading text-xl font-bold text-text-primary">{jobSeeker.full_name || 'Your job profile'}</h2>
                <p className="text-sm text-text-muted">{email}</p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Full name</span>
                <input className={inputClass} value={jobSeeker.full_name} onChange={(event) => setJobSeeker((current) => ({ ...current, full_name: event.target.value }))} placeholder="Your name" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Highest qualification</span>
                <input className={inputClass} value={jobSeeker.qualification} onChange={(event) => setJobSeeker((current) => ({ ...current, qualification: event.target.value }))} placeholder="e.g. Graduate" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Degree / course</span>
                <input className={inputClass} value={jobSeeker.degree_type} onChange={(event) => setJobSeeker((current) => ({ ...current, degree_type: event.target.value }))} placeholder="e.g. B.Com, B.Tech" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Experience (years)</span>
                <input type="number" className={inputClass} value={jobSeeker.job_experience_years} onChange={(event) => setJobSeeker((current) => ({ ...current, job_experience_years: event.target.value }))} placeholder="0" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Preferred job category</span>
                <input className={inputClass} value={jobSeeker.job_category} onChange={(event) => setJobSeeker((current) => ({ ...current, job_category: event.target.value }))} placeholder="Teaching, PSC, Banking…" />
              </label>
              <label className="block sm:col-span-2">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Skills</span>
                <input className={inputClass} value={jobSeeker.job_skills} onChange={(event) => setJobSeeker((current) => ({ ...current, job_skills: event.target.value }))} placeholder="Computer, typing, accounts (comma-separated)" />
              </label>
              <label className="block sm:col-span-2">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Languages</span>
                <input className={inputClass} value={jobSeeker.languages} onChange={(event) => setJobSeeker((current) => ({ ...current, languages: event.target.value }))} placeholder="Hindi, English" />
              </label>
            </div>

            <StatePicker selected={jobSeeker.states} onToggle={toggleJobState} accent="violet" />
            <AlertToggle checked={jobSeeker.email_alerts} onChange={(checked) => setJobSeeker((current) => ({ ...current, email_alerts: checked }))} text="Get a digest of new jobs matching your interests." />

            <div className="mt-6 flex justify-end">
              <Button onClick={saveJobSeeker} disabled={saving} className="bg-[#6C3EF4] text-white hover:bg-[#6C3EF4]/90 gap-1.5">
                {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                {saving ? 'Saving…' : 'Save Job Profile'}
              </Button>
            </div>
          </section>

          <ProfileAside role="jobseeker" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <section className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-brand-blue/30 bg-brand-blue/10">
                <Building2 className="h-6 w-6 text-brand-blue" />
              </div>
              <div>
                <h2 className="font-heading text-xl font-bold text-text-primary">{contractor.company_name || contractor.full_name || 'Your business profile'}</h2>
                <p className="text-sm text-text-muted">{email}</p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Full name</span>
                <input className={inputClass} value={contractor.full_name} onChange={(event) => setContractor((current) => ({ ...current, full_name: event.target.value }))} placeholder="Your name" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Company name</span>
                <input className={inputClass} value={contractor.company_name} onChange={(event) => setContractor((current) => ({ ...current, company_name: event.target.value }))} placeholder="Company / firm" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Contractor class</span>
                <input className={inputClass} value={contractor.contractor_class} onChange={(event) => setContractor((current) => ({ ...current, contractor_class: event.target.value }))} placeholder="e.g. Class A" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Annual turnover (₹ lakhs)</span>
                <input type="number" className={inputClass} value={contractor.turnover_lakhs} onChange={(event) => setContractor((current) => ({ ...current, turnover_lakhs: event.target.value }))} placeholder="250" />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Experience (years)</span>
                <input type="number" className={inputClass} value={contractor.experience_years} onChange={(event) => setContractor((current) => ({ ...current, experience_years: event.target.value }))} placeholder="8" />
              </label>
              <label className="block sm:col-span-2">
                <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-text-muted">Sectors of interest</span>
                <input className={inputClass} value={contractor.sectors} onChange={(event) => setContractor((current) => ({ ...current, sectors: event.target.value }))} placeholder="Civil Works, Electrical, IT (comma-separated)" />
              </label>
            </div>

            <StatePicker selected={contractor.states} onToggle={toggleContractorState} accent="blue" />
            <AlertToggle checked={contractor.email_alerts} onChange={(checked) => setContractor((current) => ({ ...current, email_alerts: checked }))} text="Get a digest of tenders matching your business." />

            <div className="mt-6 flex justify-end">
              <Button onClick={saveContractor} disabled={saving} className="bg-brand-blue text-white hover:bg-brand-blue/90 gap-1.5">
                {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                {saving ? 'Saving…' : 'Save Contractor Profile'}
              </Button>
            </div>
          </section>

          <ProfileAside role="contractor" />
        </div>
      )}
    </AppShell>
  )
}

function StatePicker({ selected, onToggle, accent }: { selected: string[]; onToggle: (state: string) => void; accent: 'blue' | 'violet' }) {
  return (
    <div className="mt-5">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-text-muted">States of interest</span>
      <div className="flex flex-wrap gap-2">
        {STATES.map((state) => {
          const active = selected.includes(state)
          return (
            <button
              key={state}
              type="button"
              onClick={() => onToggle(state)}
              className={active
                ? accent === 'violet'
                  ? 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-[#6C3EF4]/40 bg-[#6C3EF4]/10 text-[#6C3EF4]'
                  : 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-brand-blue/40 bg-brand-blue/10 text-brand-blue'
                : 'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-border-subtle bg-surface-elevated text-text-secondary hover:text-text-primary'}
            >
              <MapPin className="w-3.5 h-3.5" /> {state}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function AlertToggle({ checked, onChange, text }: { checked: boolean; onChange: (checked: boolean) => void; text: string }) {
  return (
    <div className="mt-5 flex items-center justify-between rounded-xl border border-border-subtle bg-surface-elevated px-4 py-3 gap-4">
      <div className="flex items-center gap-2.5 min-w-0">
        <Mail className="w-4 h-4 text-brand-blue flex-shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-primary">Daily email alerts</p>
          <p className="text-xs text-text-muted">{text}</p>
        </div>
      </div>
      <button type="button" role="switch" aria-checked={checked} onClick={() => onChange(!checked)} className={checked ? 'relative w-10 h-6 rounded-full bg-brand-blue transition-colors flex-shrink-0' : 'relative w-10 h-6 rounded-full bg-border-subtle transition-colors flex-shrink-0'}>
        <span className={checked ? 'absolute top-0.5 right-0.5 w-5 h-5 rounded-full bg-white transition-all' : 'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-all'} />
      </button>
    </div>
  )
}

function ProfileAside({ role }: { role: 'contractor' | 'jobseeker' }) {
  return (
    <aside className="rounded-2xl border border-border-subtle bg-surface p-6 h-fit">
      <p className="font-heading text-lg font-bold text-text-primary">Focused experience</p>
      <p className="mt-2 text-sm leading-relaxed text-text-secondary">
        {role === 'jobseeker'
          ? 'Your workspace shows jobs, application deadlines, and preparation tools without tender-related clutter.'
          : 'Your workspace shows tenders, bid preparation, and business matching without job-seeker features.'}
      </p>
      <div className="mt-5 space-y-3">
        <div className="flex items-center gap-3 rounded-xl border border-border-subtle bg-background/40 px-4 py-3">
          <ShieldCheck className="w-4 h-4 text-brand-blue flex-shrink-0" />
          <span className="text-sm text-text-secondary">Your profile remains private to your account</span>
        </div>
      </div>
      <Link href="/select-role" className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-brand-blue hover:underline">
        <RefreshCw className="w-3.5 h-3.5" /> Switch experience
      </Link>
    </aside>
  )
}
