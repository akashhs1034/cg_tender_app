'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Bookmark, BookmarkCheck, MapPin, Clock, Eye, FileText, Loader2, LogIn, Briefcase, Users, ExternalLink,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageHero } from '@/components/page-hero'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { useSaved } from '@/lib/saved-context'
import { useSavedJobs } from '@/lib/saved-jobs-context'
import { useAuth } from '@/lib/auth-context'
import { getTendersByIds, getJobsByIds } from '@/lib/data'
import { cn } from '@/lib/utils'
import type { Tender, Job } from '@/lib/mock-data'

type Tab = 'tenders' | 'jobs'

export default function SavedPage() {
  const saved = useSaved()
  const savedJobs = useSavedJobs()
  const { user } = useAuth()
  const { toast } = useToast()
  const [tab, setTab] = useState<Tab>('tenders')
  const [tenders, setTenders] = useState<Tender[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  const tenderKey = [...saved.savedIds].sort().join(',')
  const jobKey = [...savedJobs.savedIds].sort().join(',')

  useEffect(() => {
    if (!saved.ready) return
    let active = true
    getTendersByIds([...saved.savedIds]).then((r) => active && setTenders(r))
    return () => {
      active = false
    }
  }, [tenderKey, saved.ready]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!savedJobs.ready) return
    let active = true
    getJobsByIds([...savedJobs.savedIds]).then((r) => active && setJobs(r))
    return () => {
      active = false
    }
  }, [jobKey, savedJobs.ready]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (saved.ready && savedJobs.ready) setLoading(false)
  }, [saved.ready, savedJobs.ready])

  const removeTender = async (t: Tender) => {
    await saved.toggleSaved(t)
    setTenders((prev) => prev.filter((x) => x.id !== t.id))
    toast('Removed from saved', 'info')
  }
  const removeJob = async (j: Job) => {
    await savedJobs.toggleSaved(j)
    setJobs((prev) => prev.filter((x) => x.id !== j.id))
    toast('Removed from saved', 'info')
  }

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: 'tenders', label: 'Tenders', count: tenders.length },
    { id: 'jobs', label: 'Jobs', count: jobs.length },
  ]

  return (
    <AppShell pageTitle="Saved" pageSubtitle="Your saved tenders and jobs pipeline">
      <PageHero
        variant="dashboard"
        eyebrow="My Pipeline"
        icon={<Bookmark className="h-3.5 w-3.5" />}
        title="Saved Opportunities"
        subtitle={
          user
            ? 'Tenders and jobs you have saved, synced to your account across devices.'
            : 'Saved on this device. Sign in to sync everywhere.'
        }
      >
        {!user && (
          <Link href="/login" className="btn-glow inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-xs font-semibold text-white transition-colors hover:bg-brand-blue/90">
            <LogIn className="h-3.5 w-3.5" /> Sign in to sync
          </Link>
        )}
      </PageHero>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-xl bg-surface border border-border-subtle w-fit mb-6">
        {tabs.map((tb) => (
          <button key={tb.id} onClick={() => setTab(tb.id)}
            className={cn('px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-150',
              tab === tb.id ? 'bg-brand-blue text-white' : 'text-text-secondary hover:text-text-primary')}>
            {tb.label} <span className="opacity-70">({tb.count})</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-text-muted">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading your saved items…
        </div>
      ) : tab === 'tenders' ? (
        tenders.length === 0 ? (
          <EmptyState icon={Bookmark} title="No saved tenders yet" sub="Tap the bookmark on any tender to add it here." href="/tenders" cta="Browse Tenders" />
        ) : (
          <div className="grid gap-4">
            {tenders.map((t) => (
              <div key={t.id} className="rounded-2xl card-premium hover-lift p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <BadgeMode mode={t.mode} />
                      <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{t.category}</span>
                    </div>
                    <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{t.title}</h3>
                  </div>
                  <AiMatchBadge score={t.aiMatchScore} className="flex-shrink-0 mt-1" />
                </div>
                <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{t.district}, {t.state === 'Chhattisgarh' ? 'CG' : 'UP'}</span>
                  <span className="font-semibold text-text-primary">{t.estimatedValue}</span>
                  <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {t.deadline}</span></span>
                </div>
                <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
                  <Link href={`/tenders/${t.id}`}>
                    <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs h-8 gap-1.5"><Eye className="w-3.5 h-3.5" /> View Details</Button>
                  </Link>
                  {t.documentUrl && (
                    <a href={t.documentUrl} target="_blank" rel="noopener noreferrer">
                      <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5"><FileText className="w-3.5 h-3.5" /> Document</Button>
                    </a>
                  )}
                  <Button size="sm" variant="outline" onClick={() => removeTender(t)} className="border-brand-blue/40 text-brand-blue bg-brand-blue/10 hover:bg-brand-blue/15 text-xs h-8 gap-1.5"><BookmarkCheck className="w-3.5 h-3.5" /> Saved</Button>
                </div>
              </div>
            ))}
          </div>
        )
      ) : jobs.length === 0 ? (
        <EmptyState icon={Briefcase} title="No saved jobs yet" sub="Tap the bookmark on any job to add it here." href="/jobs" cta="Browse Jobs" />
      ) : (
        <div className="grid gap-4">
          {jobs.map((j) => (
            <div key={j.id} className="rounded-2xl card-premium hover-lift-violet p-5">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <BadgeMode mode={j.mode} />
                    <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{j.category}</span>
                  </div>
                  <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{j.title}</h3>
                  <p className="text-xs text-text-muted mt-1">{j.department}</p>
                </div>
                <AiMatchBadge score={j.matchScore} className="flex-shrink-0 mt-1" />
              </div>
              <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{j.district}, {j.state === 'Chhattisgarh' ? 'CG' : 'UP'}</span>
                {j.vacancies > 0 && <span className="flex items-center gap-1"><Users className="w-3 h-3 text-[#6C3EF4]" />{j.vacancies.toLocaleString()}</span>}
                <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {j.deadline}</span></span>
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
                <Link href={`/jobs/${j.id}`}>
                  <Button size="sm" className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold text-xs h-8 gap-1.5"><Eye className="w-3.5 h-3.5" /> View Details</Button>
                </Link>
                {j.applyUrl && (
                  <a href={j.applyUrl} target="_blank" rel="noopener noreferrer">
                    <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5"><ExternalLink className="w-3.5 h-3.5" /> Apply</Button>
                  </a>
                )}
                <Button size="sm" variant="outline" onClick={() => removeJob(j)} className="border-[#6C3EF4]/40 text-[#6C3EF4] bg-[#6C3EF4]/10 hover:bg-[#6C3EF4]/15 text-xs h-8 gap-1.5"><BookmarkCheck className="w-3.5 h-3.5" /> Saved</Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </AppShell>
  )
}

function EmptyState({ icon: Icon, title, sub, href, cta }: { icon: React.ElementType; title: string; sub: string; href: string; cta: string }) {
  return (
    <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
      <Icon className="w-8 h-8 text-text-muted mx-auto mb-3" />
      <p className="text-text-secondary font-medium">{title}</p>
      <p className="text-sm text-text-muted mt-1">{sub}</p>
      <Link href={href} className="inline-flex items-center gap-1.5 mt-4 rounded-lg bg-brand-blue px-4 py-2 text-xs font-semibold text-white hover:bg-brand-blue/90 transition-colors">
        <FileText className="h-3.5 w-3.5" /> {cta}
      </Link>
    </div>
  )
}
