'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Bookmark,
  BookmarkCheck,
  MapPin,
  Clock,
  Eye,
  FileText,
  Loader2,
  LogIn,
  Briefcase,
  Users,
  ExternalLink,
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
import type { Tender, Job } from '@/lib/mock-data'

export default function SavedPage() {
  const saved = useSaved()
  const savedJobs = useSavedJobs()
  const { user, role } = useAuth()
  const { toast } = useToast()
  const [tenders, setTenders] = useState<Tender[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  const tenderKey = [...saved.savedIds].sort().join(',')
  const jobKey = [...savedJobs.savedIds].sort().join(',')

  useEffect(() => {
    let active = true

    async function loadSavedItems() {
      if (!role) {
        if (active) setLoading(false)
        return
      }

      setLoading(true)
      if (role === 'contractor') {
        if (!saved.ready) return
        const rows = await getTendersByIds([...saved.savedIds])
        if (active) {
          setTenders(rows)
          setLoading(false)
        }
      } else {
        if (!savedJobs.ready) return
        const rows = await getJobsByIds([...savedJobs.savedIds])
        if (active) {
          setJobs(rows)
          setLoading(false)
        }
      }
    }

    void loadSavedItems()

    return () => {
      active = false
    }
  }, [role, tenderKey, jobKey, saved.ready, savedJobs.ready]) // eslint-disable-line react-hooks/exhaustive-deps

  const removeTender = async (tender: Tender) => {
    await saved.toggleSaved(tender)
    setTenders((current) => current.filter((item) => item.id !== tender.id))
    toast('Removed from saved', 'info')
  }

  const removeJob = async (job: Job) => {
    await savedJobs.toggleSaved(job)
    setJobs((current) => current.filter((item) => item.id !== job.id))
    toast('Removed from saved', 'info')
  }

  if (user && !role) {
    return (
      <AppShell pageTitle="Saved" pageSubtitle="Choose your experience first">
        <EmptyState icon={Bookmark} title="Choose your OPPORTA experience" sub="Select Contractor or Job Seeker so we can show the correct saved items." href="/select-role" cta="Choose Experience" />
      </AppShell>
    )
  }

  const isJobSeeker = role === 'jobseeker'
  const title = isJobSeeker ? 'Saved Jobs' : 'Saved Tenders'
  const subtitle = isJobSeeker
    ? 'Government jobs you want to review or apply for'
    : 'Tenders saved to your opportunity pipeline'

  return (
    <AppShell pageTitle={title} pageSubtitle={subtitle} bg={isJobSeeker ? 'jobs' : 'tenders'}>
      <PageHero
        variant={isJobSeeker ? 'jobs' : 'tenders'}
        eyebrow="My Pipeline"
        icon={<Bookmark className="h-3.5 w-3.5" />}
        title={title}
        subtitle={user ? subtitle : 'Saved on this device. Sign in to sync across devices.'}
      >
        {!user && (
          <Link href="/login" className="btn-glow inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-xs font-semibold text-white transition-colors hover:bg-brand-blue/90">
            <LogIn className="h-3.5 w-3.5" /> Sign in to sync
          </Link>
        )}
      </PageHero>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-text-muted">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading your saved items…
        </div>
      ) : isJobSeeker ? (
        jobs.length === 0 ? (
          <EmptyState icon={Briefcase} title="No saved jobs yet" sub="Tap the bookmark on any job to add it here." href="/jobs" cta="Browse Jobs" />
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <div key={job.id} className="rounded-2xl card-premium hover-lift-violet p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <BadgeMode mode={job.mode} />
                      <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{job.category}</span>
                    </div>
                    <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{job.title}</h3>
                    <p className="text-xs text-text-muted mt-1">{job.department}</p>
                  </div>
                  <AiMatchBadge score={job.matchScore} className="flex-shrink-0 mt-1" />
                </div>
                <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.district}, {job.state === 'Chhattisgarh' ? 'CG' : 'UP'}</span>
                  {job.vacancies > 0 && <span className="flex items-center gap-1"><Users className="w-3 h-3 text-[#6C3EF4]" />{job.vacancies.toLocaleString()}</span>}
                  <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {job.deadline}</span></span>
                </div>
                <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
                  <Link href={`/jobs/${job.id}`}>
                    <Button size="sm" className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold text-xs h-8 gap-1.5"><Eye className="w-3.5 h-3.5" /> View Details</Button>
                  </Link>
                  {job.applyUrl && (
                    <a href={job.applyUrl} target="_blank" rel="noopener noreferrer">
                      <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5"><ExternalLink className="w-3.5 h-3.5" /> Apply</Button>
                    </a>
                  )}
                  <Button size="sm" variant="outline" onClick={() => removeJob(job)} className="border-[#6C3EF4]/40 text-[#6C3EF4] bg-[#6C3EF4]/10 hover:bg-[#6C3EF4]/15 text-xs h-8 gap-1.5"><BookmarkCheck className="w-3.5 h-3.5" /> Saved</Button>
                </div>
              </div>
            ))}
          </div>
        )
      ) : tenders.length === 0 ? (
        <EmptyState icon={Bookmark} title="No saved tenders yet" sub="Tap the bookmark on any tender to add it here." href="/tenders" cta="Browse Tenders" />
      ) : (
        <div className="grid gap-4">
          {tenders.map((tender) => (
            <div key={tender.id} className="rounded-2xl card-premium hover-lift p-5">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <BadgeMode mode={tender.mode} />
                    <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{tender.category}</span>
                  </div>
                  <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{tender.title}</h3>
                </div>
                <AiMatchBadge score={tender.aiMatchScore} className="flex-shrink-0 mt-1" />
              </div>
              <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{tender.district}, {tender.state === 'Chhattisgarh' ? 'CG' : 'UP'}</span>
                <span className="font-semibold text-text-primary">{tender.estimatedValue}</span>
                <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {tender.deadline}</span></span>
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
                <Link href={`/tenders/${tender.id}`}>
                  <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs h-8 gap-1.5"><Eye className="w-3.5 h-3.5" /> View Details</Button>
                </Link>
                {tender.documentUrl && (
                  <a href={tender.documentUrl} target="_blank" rel="noopener noreferrer">
                    <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5"><FileText className="w-3.5 h-3.5" /> Document</Button>
                  </a>
                )}
                <Button size="sm" variant="outline" onClick={() => removeTender(tender)} className="border-brand-blue/40 text-brand-blue bg-brand-blue/10 hover:bg-brand-blue/15 text-xs h-8 gap-1.5"><BookmarkCheck className="w-3.5 h-3.5" /> Saved</Button>
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
        {cta}
      </Link>
    </div>
  )
}
