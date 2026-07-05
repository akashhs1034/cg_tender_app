'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Search, X, MapPin, CalendarClock, Users, GraduationCap, BookOpen,
  PlayCircle, ExternalLink, Lightbulb, ChevronDown,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { DemoBanner } from '@/components/demo-banner'
import { PageHero } from '@/components/page-hero'
import { PageTabs } from '@/components/page-tabs'
import { BadgeMode } from '@/components/ui/badge-mode'
import { Button } from '@/components/ui/button'
import { JOB_CATEGORIES, getDistricts, matchesJobCategory } from '@/lib/mock-data'
import type { State, Job } from '@/lib/mock-data'
import { matchExamResources, EXAM_RESOURCES } from '@/lib/study-resources'
import { useLanguage } from '@/lib/language-context'
import type { StudyLink } from '@/lib/study-resources'
import { cn } from '@/lib/utils'

function linkIcon(kind: StudyLink['kind']) {
  if (kind === 'youtube') return <PlayCircle className="w-3.5 h-3.5 text-[#FF0000]" />
  if (kind === 'practice') return <BookOpen className="w-3.5 h-3.5 text-[#6C3EF4]" />
  return <ExternalLink className="w-3.5 h-3.5 text-text-muted" />
}

const states: Array<State | 'All'> = ['All', 'Chhattisgarh', 'Uttar Pradesh']
const categories = [...JOB_CATEGORIES]

export function ExamPlannerClient({ jobs }: { jobs: Job[] }) {
  const [search, setSearch] = useState('')
  const [stateFilter, setStateFilter] = useState<State | 'All'>('All')
  const [districtFilter, setDistrictFilter] = useState('All')
  const [catFilter, setCatFilter] = useState('All')
  const [focusId, setFocusId] = useState<string | null>(null)
  const [openPlan, setOpenPlan] = useState<string | null>(null)
  const { t } = useLanguage()

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('jobId')
    if (id && jobs.some((j) => j.id === id)) setFocusId(id)
  }, [jobs])

  const focusedJob = focusId ? jobs.find((j) => j.id === focusId) ?? null : null

  const q = search.trim().toLowerCase()
  const filtered = jobs.filter((j) => {
    if (focusId) return j.id === focusId
    if (q && !j.advNumber.toLowerCase().includes(q) && !j.title.toLowerCase().includes(q)) return false
    if (stateFilter !== 'All' && j.state !== stateFilter) return false
    if (districtFilter !== 'All' && j.district !== districtFilter) return false
    if (!matchesJobCategory(j.category, catFilter)) return false
    return true
  })

  return (
    <AppShell pageTitle={t('exam_planner')} pageSubtitle={t('plan_prep')} bg="jobs">
      <DemoBanner>Job listings are live. Open “Study Plan &amp; Resources” on any notification for curated prep material and YouTube channels for that exam.</DemoBanner>
      <PageHero
        variant="jobs"
        eyebrow="Exam Planner"
        icon={<GraduationCap className="h-3.5 w-3.5" />}
        title={t('exam_planner')}
        subtitle={t('plan_prep_long')}
      />
      <PageTabs
        accent="purple"
        tabs={[
          { label: t('government_jobs'), href: '/jobs' },
          { label: t('exam_planner'), href: '/exam-planner' },
        ]}
      />

      {focusedJob && (
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#6C3EF4]/25 bg-[#6C3EF4]/5 px-4 py-3">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-[#6C3EF4]">{t('study_plan')}</p>
            <p className="truncate text-sm font-semibold text-text-primary">{focusedJob.title}</p>
            <p className="text-xs text-text-muted">{focusedJob.advNumber}</p>
          </div>
          <button
            onClick={() => setFocusId(null)}
            className="flex items-center gap-1.5 rounded-md border border-border-subtle px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:bg-surface-elevated hover:text-text-primary"
          >
            <X className="h-3.5 w-3.5" /> {t('show_all_notifications')}
          </button>
        </div>
      )}

      {/* Job selector / filter area */}
      {!focusId && (
      <div className="mb-5 p-4 rounded-xl border border-border-subtle bg-surface">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder={t('search_adv')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-[#6C3EF4] transition-colors"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2" aria-label="Clear search">
              <X className="w-3.5 h-3.5 text-text-muted" />
            </button>
          )}
        </div>
        <div className="flex flex-wrap gap-4">
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">{t('state')}</p>
            <div className="flex gap-1.5 flex-wrap">
              {states.map((s) => (
                <button key={s} onClick={() => { setStateFilter(s); setDistrictFilter('All') }}
                  className={cn('px-3 py-1 rounded-md text-xs font-medium border transition-colors',
                    stateFilter === s ? 'bg-[#6C3EF4]/15 text-[#6C3EF4] border-[#6C3EF4]/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">{t('district')}</p>
            <select
              value={districtFilter}
              onChange={(e) => setDistrictFilter(e.target.value)}
              disabled={stateFilter === 'All'}
              aria-label="Filter by district"
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-[#6C3EF4] disabled:opacity-50 disabled:cursor-not-allowed min-w-[150px]"
            >
              <option value="All">{t('all_districts')}</option>
              {getDistricts(stateFilter).map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            {stateFilter === 'All' && <p className="text-[10px] text-text-muted mt-1">{t('select_state_first')}</p>}
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">{t('job_category')}</p>
            <select
              value={catFilter}
              onChange={(e) => setCatFilter(e.target.value)}
              aria-label="Filter by job category"
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-[#6C3EF4] min-w-[170px]"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c === 'All' ? t('all_categories') : c}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      )}

      <p className="text-xs text-text-muted mb-4">{t('showing')} {filtered.length} {t('of')} {jobs.length} {t('notifications')}</p>

      {/* Exam plan cards */}
      <div className="grid gap-4">
        {jobs.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <GraduationCap className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">{t('no_notifications')}</p>
            <p className="text-sm text-text-muted mt-1">{t('check_back')}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <GraduationCap className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">{t('no_match_selection')}</p>
            <p className="text-sm text-text-muted mt-1">{t('adjust_selection')}</p>
          </div>
        ) : (
          filtered.map((j) => (
            <div key={j.id} className="rounded-2xl border border-border-subtle bg-surface p-5 hover:border-[#6C3EF4]/25 transition-colors">
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <BadgeMode mode={j.mode} />
                <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{j.category}</span>
              </div>
              <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{j.title}</h3>
              <p className="text-xs text-text-muted mt-1">{j.advNumber}</p>

              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-text-secondary">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{j.district}, {j.state}</span>
                {j.vacancies > 0 && <span className="flex items-center gap-1"><Users className="w-3 h-3 text-[#6C3EF4]" />{j.vacancies.toLocaleString()} {t('posts')}</span>}
                <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />{j.qualification}</span>
              </div>

              {/* Exam timeline */}
              <div className="mt-4 flex flex-wrap gap-3">
                <div className="flex-1 min-w-[150px] rounded-lg border border-[#6C3EF4]/20 bg-[#6C3EF4]/5 px-3 py-2.5">
                  <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide">{t('exam_date')}</p>
                  <p className="text-sm font-semibold text-text-primary flex items-center gap-1.5 mt-0.5">
                    <CalendarClock className="w-3.5 h-3.5 text-[#6C3EF4]" />{j.examDate ?? 'To be announced'}
                  </p>
                </div>
                <div className="flex-1 min-w-[150px] rounded-lg border border-border-subtle bg-surface-elevated px-3 py-2.5">
                  <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide">{t('apply_before')}</p>
                  <p className="text-sm font-semibold text-danger mt-0.5">{j.deadline}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-4 mt-4 border-t border-border-subtle">
                <Link href={`/jobs/${j.id}`}>
                  <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                    <BookOpen className="w-3.5 h-3.5" /> {t('view_job')}
                  </Button>
                </Link>
                {j.applyUrl && (
                  <a href={j.applyUrl} target="_blank" rel="noopener noreferrer">
                    <Button size="sm" className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold text-xs h-8 gap-1.5">
                      <GraduationCap className="w-3.5 h-3.5" /> {t('apply')}
                    </Button>
                  </a>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setOpenPlan(openPlan === j.id ? null : j.id)}
                  className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5"
                >
                  <GraduationCap className="w-3.5 h-3.5" /> {t('study_plan_resources')}
                  <ChevronDown className={cn('w-3.5 h-3.5 transition-transform', openPlan === j.id && 'rotate-180')} />
                </Button>
              </div>

              {/* Study resources panel */}
              {openPlan === j.id && (() => {
                const kit = matchExamResources(j.title, j.department)
                return (
                  <div className="mt-4 rounded-xl border border-[#6C3EF4]/25 bg-[#6C3EF4]/5 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-[#6C3EF4] mb-1">
                      {kit.name}
                    </p>
                    <p className="text-xs text-text-secondary flex items-start gap-1.5 mb-3">
                      <Lightbulb className="w-3.5 h-3.5 text-warning flex-shrink-0 mt-0.5" />
                      {kit.tip}
                    </p>
                    <div className="grid sm:grid-cols-2 gap-1.5">
                      {kit.links.map((l) => (
                        <a
                          key={l.url + l.label}
                          href={l.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 rounded-lg border border-border-subtle bg-surface px-3 py-2 text-xs text-text-secondary hover:text-text-primary hover:border-[#6C3EF4]/40 transition-colors"
                        >
                          {linkIcon(l.kind)}
                          <span className="truncate">{l.label}</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )
              })()}
            </div>
          ))
        )}
      </div>

      {/* ── Full Study Resources hub ── */}
      <div className="mt-10">
        <div className="mb-4">
          <h2 className="font-heading font-semibold text-lg text-text-primary flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#6C3EF4]" /> {t('study_resources')}
          </h2>
          <p className="text-sm text-text-muted mt-0.5">
            {t('study_resources_sub')}
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          {EXAM_RESOURCES.map((kit) => (
            <div key={kit.key} className="rounded-2xl border border-border-subtle bg-surface p-5">
              <p className="font-heading font-semibold text-sm text-text-primary">{kit.name}</p>
              <p className="text-xs text-text-secondary flex items-start gap-1.5 mt-1.5 mb-3">
                <Lightbulb className="w-3.5 h-3.5 text-warning flex-shrink-0 mt-0.5" />
                {kit.tip}
              </p>
              <div className="grid gap-1.5">
                {kit.links.map((l) => (
                  <a
                    key={l.url + l.label}
                    href={l.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-lg border border-border-subtle bg-surface-elevated px-3 py-2 text-xs text-text-secondary hover:text-text-primary hover:border-[#6C3EF4]/40 transition-colors"
                  >
                    {linkIcon(l.kind)}
                    <span className="truncate">{l.label}</span>
                    <ExternalLink className="w-3 h-3 ml-auto opacity-40 flex-shrink-0" />
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  )
}
