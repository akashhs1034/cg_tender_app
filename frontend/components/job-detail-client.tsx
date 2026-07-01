'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  ChevronLeft, MapPin, Clock, Users, ExternalLink, BookOpen,
  CheckCircle2, XCircle, Sparkles, Calendar,
  Shield, FileText, History, TrendingUp, Target, Brain,
  ClipboardList, CalendarDays, GraduationCap, Star, Download, Bookmark, BookmarkCheck,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import type { Job } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { useSavedJobs } from '@/lib/saved-jobs-context'

const tabs = [
  { id: 'overview', label: 'Overview', icon: BookOpen },
  { id: 'eligibility', label: 'Eligibility', icon: Shield },
  { id: 'dates', label: 'Important Dates', icon: Calendar },
  { id: 'vacancies', label: 'Vacancy Details', icon: Users },
  { id: 'salary', label: 'Salary', icon: TrendingUp },
  { id: 'application', label: 'Application Process', icon: FileText },
  { id: 'match', label: 'Resume/Profile Match', icon: Sparkles },
  { id: 'planner', label: 'Exam Planner', icon: Brain },
  { id: 'study', label: 'Study Checklist', icon: ClipboardList },
  { id: 'source', label: 'Source History', icon: History },
]

export function JobDetailClient({ job }: { job: Job }) {
  const [activeTab, setActiveTab] = useState('overview')
  const { toast } = useToast()
  const { isSaved, toggleSaved } = useSavedJobs()
  const hasVacancies = job.vacancies > 0
  const hasSelection = job.selectionProcess.length > 0
  const applyHref = job.applyUrl ?? job.documentUrl
  const saved = isSaved(job.id)

  const handleSave = async () => {
    const nowSaved = await toggleSaved(job)
    if (nowSaved) toast('Saved', 'success', { description: job.title })
    else toast('Removed from saved', 'info')
  }

  const applyExternal = () =>
    toast('Application link unavailable', 'info', { description: 'No official link was found for this posting yet.' })

  return (
    <AppShell>
      {/* Back + Title */}
      <div className="mb-6">
        <Link href="/jobs" className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text-secondary transition-colors mb-4">
          <ChevronLeft className="w-4 h-4" /> Back to Jobs
        </Link>
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <BadgeMode mode={job.mode} />
              <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded border border-border-subtle">{job.category}</span>
              <AiMatchBadge score={job.matchScore} />
            </div>
            <h1 className="font-heading font-bold text-xl lg:text-2xl text-text-primary leading-snug text-balance">{job.title}</h1>
            <p className="text-sm text-text-muted mt-1">{job.advNumber}</p>
          </div>
          <div className="flex flex-wrap gap-2 flex-shrink-0">
            {applyHref ? (
              <a href={applyHref} target="_blank" rel="noopener noreferrer">
                <Button size="sm" className="btn-glow bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold gap-1.5">
                  <ExternalLink className="w-3.5 h-3.5" /> Apply Now
                </Button>
              </a>
            ) : (
              <Button size="sm" onClick={applyExternal} className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold gap-1.5">
                <ExternalLink className="w-3.5 h-3.5" /> Apply Now
              </Button>
            )}
            {job.documentUrl && (
              <a href={job.documentUrl} target="_blank" rel="noopener noreferrer">
                <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:bg-surface-elevated gap-1.5">
                  <Download className="w-3.5 h-3.5" /> Notification
                </Button>
              </a>
            )}
            <Button size="sm" variant="outline" onClick={handleSave} aria-pressed={saved}
              className={cn('gap-1.5', saved ? 'border-[#6C3EF4]/40 text-[#6C3EF4] bg-[#6C3EF4]/10' : 'border-border-subtle text-text-secondary hover:bg-surface-elevated')}>
              {saved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />} {saved ? 'Saved' : 'Save'}
            </Button>
            <Button size="sm" variant="outline" onClick={() => setActiveTab('match')} className="border-border-subtle text-text-secondary hover:bg-surface-elevated gap-1.5">
              <Target className="w-3.5 h-3.5" /> Check My Match
            </Button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <span className="flex items-center gap-1.5 text-text-secondary"><BookOpen className="w-3.5 h-3.5 text-text-muted" />{job.department}</span>
          <span className="flex items-center gap-1.5 text-text-secondary"><MapPin className="w-3.5 h-3.5 text-text-muted" />{job.district}, {job.state}</span>
          {hasVacancies && (
            <span className="flex items-center gap-1.5 text-text-primary font-semibold"><Users className="w-3.5 h-3.5 text-[#6C3EF4]" />{job.vacancies.toLocaleString()} Vacancies</span>
          )}
          <span className="flex items-center gap-1.5 text-danger font-medium"><Clock className="w-3.5 h-3.5" />Deadline: {job.deadline}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 mb-6 border-b border-border-subtle">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-xs font-semibold whitespace-nowrap transition-colors',
              activeTab === tab.id
                ? 'text-[#6C3EF4] border-b-2 border-[#6C3EF4] -mb-px bg-[#6C3EF4]/5'
                : 'text-text-muted hover:text-text-secondary hover:bg-surface-elevated'
            )}
          >
            <tab.icon className="w-3.5 h-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {/* Overview */}
        {activeTab === 'overview' && (
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-5">
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <h3 className="font-heading font-semibold text-sm text-text-primary mb-3">About this Job</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{job.description}</p>
              </div>
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <h3 className="font-heading font-semibold text-sm text-text-primary mb-3">Quick Details</h3>
                <dl className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Adv. Number', value: job.advNumber },
                    { label: 'State', value: job.state },
                    { label: 'District', value: job.district },
                    { label: 'Mode', value: job.mode },
                    { label: 'Category', value: job.category },
                    { label: 'Qualification', value: job.qualification },
                    { label: 'Age Limit', value: job.ageLimit },
                    { label: 'Salary', value: job.salary },
                    { label: 'Exam Date', value: job.examDate ?? 'To be announced' },
                  ].map((item) => (
                    <div key={item.label}>
                      <dt className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">{item.label}</dt>
                      <dd className="text-xs text-text-secondary">{item.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
            <div className="space-y-4">
              <div className="rounded-xl border border-[#6C3EF4]/20 bg-[#6C3EF4]/5 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-[#6C3EF4]" />
                  <p className="text-sm font-semibold text-[#6C3EF4]">Profile Match</p>
                </div>
                <div className="flex items-end gap-2 mb-2">
                  <p className="text-4xl font-heading font-bold text-text-primary">{job.matchScore}%</p>
                  <p className="text-xs text-success mb-1">{job.matchScore >= 85 ? 'Excellent' : job.matchScore >= 70 ? 'Good' : 'Fair'} match</p>
                </div>
                <div className="h-2 rounded-full bg-surface-elevated overflow-hidden">
                  <div className="h-full bg-[#6C3EF4] rounded-full" style={{ width: `${job.matchScore}%` }} />
                </div>
                <button onClick={() => setActiveTab('match')} className="mt-3 text-xs font-semibold text-[#6C3EF4] hover:underline">View full analysis →</button>
              </div>
              {hasSelection && (
                <div className="rounded-xl border border-border-subtle bg-surface p-5">
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Selection Process</p>
                  <ol className="space-y-2">
                    {job.selectionProcess.map((step, i) => (
                      <li key={i} className="flex items-center gap-2.5 text-xs text-text-secondary">
                        <span className="w-5 h-5 rounded-full bg-surface-elevated border border-border-subtle flex items-center justify-center text-[10px] font-bold text-text-muted flex-shrink-0">{i + 1}</span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Eligibility */}
        {activeTab === 'eligibility' && (
          <div className="max-w-2xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Eligibility Criteria</h3>
              <ul className="space-y-3">
                {job.eligibility.map((e, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-text-secondary">
                    <CheckCircle2 className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Important Dates */}
        {activeTab === 'dates' && (
          <div className="max-w-lg">
            <div className="rounded-xl border border-border-subtle bg-surface p-6 space-y-4">
              {[
                { label: 'Last Date to Apply', date: job.deadline, highlight: true },
                { label: 'Exam Date', date: job.examDate ?? 'To be announced', highlight: !!job.examDate },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-3 border-b border-border-subtle last:border-0">
                  <div className="flex items-center gap-2">
                    <CalendarDays className="w-4 h-4 text-text-muted" />
                    <span className="text-sm text-text-secondary">{item.label}</span>
                  </div>
                  <span className={cn('text-sm font-semibold', item.highlight ? 'text-danger' : 'text-text-primary')}>{item.date}</span>
                </div>
              ))}
              <p className="text-xs text-text-muted">Notification, admit card, and result dates are listed in the official notification.</p>
            </div>
          </div>
        )}

        {/* Vacancy Details */}
        {activeTab === 'vacancies' && (
          <div className="max-w-xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Vacancy Breakdown</h3>
              {hasVacancies ? (
                <>
                  <div className="mb-4 p-4 rounded-lg bg-surface-elevated border border-border-subtle flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-[#6C3EF4]/10 flex items-center justify-center">
                      <Users className="w-6 h-6 text-[#6C3EF4]" />
                    </div>
                    <div>
                      <p className="text-3xl font-heading font-bold text-text-primary">{job.vacancies.toLocaleString()}</p>
                      <p className="text-xs text-text-muted">Total Vacancies</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {[
                      { category: 'General (UR)', count: Math.round(job.vacancies * 0.5) },
                      { category: 'OBC', count: Math.round(job.vacancies * 0.27) },
                      { category: 'SC', count: Math.round(job.vacancies * 0.15) },
                      { category: 'ST', count: Math.round(job.vacancies * 0.075) },
                      { category: 'EWS', count: Math.round(job.vacancies * 0.1) },
                    ].map((row) => (
                      <div key={row.category} className="flex items-center justify-between px-3 py-2 rounded-lg bg-surface-elevated text-sm">
                        <span className="text-text-secondary">{row.category}</span>
                        <span className="font-semibold text-text-primary">{row.count}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-text-muted mt-3">* Indicative distribution. Refer to official notification for exact figures.</p>
                </>
              ) : (
                <p className="text-sm text-text-muted">Vacancy count not specified in the source. Refer to the official notification for details.</p>
              )}
            </div>
          </div>
        )}

        {/* Salary */}
        {activeTab === 'salary' && (
          <div className="max-w-lg">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Salary & Pay Scale</h3>
              <div className="p-5 rounded-xl bg-success/5 border border-success/20 mb-4">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-1">Basic Pay Range</p>
                <p className="text-2xl font-heading font-bold text-success">{job.salary}</p>
              </div>
              <div className="space-y-3 text-sm">
                {[
                  { label: 'Pay Level', value: 'As per 7th Pay Commission' },
                  { label: 'Dearness Allowance (DA)', value: 'As per applicable state norms' },
                  { label: 'House Rent Allowance (HRA)', value: '8% – 24% of Basic Pay' },
                  { label: 'Medical Allowance', value: 'Included as per state rules' },
                  { label: 'Probation Period', value: '2 years' },
                ].map((item) => (
                  <div key={item.label} className="flex items-start justify-between gap-4">
                    <span className="text-text-muted">{item.label}</span>
                    <span className="text-text-secondary text-right">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Application Process */}
        {activeTab === 'application' && (
          <div className="max-w-2xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">How to Apply</h3>
              <ol className="space-y-4">
                {[
                  'Visit the official website of the recruiting board and find the notification.',
                  'Read the official notification PDF carefully to verify eligibility.',
                  `Fill the online application form before ${job.deadline}.`,
                  'Upload required documents: photo, signature, educational certificates, and caste certificate (if applicable).',
                  'Pay the application fee online (if applicable) and submit the form.',
                  'Save the acknowledgment number and download the confirmation receipt.',
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-[#6C3EF4]/10 border border-[#6C3EF4]/20 flex items-center justify-center text-xs font-bold text-[#6C3EF4] flex-shrink-0">{i + 1}</span>
                    <p className="text-sm text-text-secondary leading-relaxed">{step}</p>
                  </li>
                ))}
              </ol>
              <div className="mt-5">
                {applyHref ? (
                  <a href={applyHref} target="_blank" rel="noopener noreferrer">
                    <Button className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold gap-1.5">
                      <ExternalLink className="w-4 h-4" /> Apply on Official Website
                    </Button>
                  </a>
                ) : (
                  <Button onClick={applyExternal} className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold gap-1.5">
                    <ExternalLink className="w-4 h-4" /> Apply on Official Website
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Resume / Profile Match */}
        {activeTab === 'match' && (
          <div className="space-y-5 max-w-2xl">
            <div className="rounded-xl border border-[#6C3EF4]/25 bg-[#6C3EF4]/5 p-5">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="w-4 h-4 text-[#6C3EF4]" />
                <h3 className="font-heading font-semibold text-sm text-text-primary">AI Resume / Profile Match</h3>
              </div>
              <p className="text-xs text-text-muted">Your profile is compared against this job&apos;s requirements.</p>
            </div>
            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center gap-5">
                <div className="relative w-24 h-24 flex-shrink-0">
                  <svg className="w-24 h-24 -rotate-90" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3.5" />
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="#6C3EF4" strokeWidth="3.5"
                      strokeDasharray={`${job.matchScore} ${100 - job.matchScore}`} strokeLinecap="round" />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center font-heading font-bold text-xl text-text-primary">{job.matchScore}%</span>
                </div>
                <div>
                  <p className="font-heading font-bold text-lg text-text-primary">
                    {job.matchScore >= 85 ? 'Excellent Match' : job.matchScore >= 70 ? 'Good Match' : 'Fair Match'}
                  </p>
                  <p className="text-xs text-text-muted mt-1">Complete your profile to refine this score.</p>
                </div>
              </div>
            </div>
            <div className="rounded-xl border border-border-subtle bg-surface p-5 space-y-3">
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wide">Match Breakdown</p>
              {[
                { label: 'Qualification Match', met: true, detail: `Required: ${job.qualification}` },
                { label: 'Age Eligibility', met: true, detail: `Age limit: ${job.ageLimit}` },
                { label: 'State Domicile', met: true, detail: `${job.state} posting` },
                { label: 'Experience', met: true, detail: 'Check the notification for experience requirements' },
              ].map((row) => (
                <div key={row.label} className="flex items-start gap-3 py-2.5 border-b border-border-subtle last:border-0">
                  {row.met ? <CheckCircle2 className="w-4 h-4 text-success mt-0.5 flex-shrink-0" /> : <XCircle className="w-4 h-4 text-danger mt-0.5 flex-shrink-0" />}
                  <div>
                    <p className="text-sm text-text-primary font-medium">{row.label}</p>
                    <p className="text-xs text-text-muted mt-0.5">{row.detail}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-brand-blue/20 bg-brand-blue/5 p-5">
              <div className="flex items-start gap-2.5">
                <Target className="w-4 h-4 text-brand-blue mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-text-primary">Suggested Next Step</p>
                  <p className="text-xs text-text-muted mt-1">Complete your profile and upload your certificates to improve your match score, then apply before the deadline.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Exam Planner */}
        {activeTab === 'planner' && (
          <div className="space-y-5">
            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center gap-2 mb-4">
                <Brain className="w-4 h-4 text-[#6C3EF4]" />
                <h3 className="font-heading font-semibold text-sm text-text-primary">Exam Preparation Planner</h3>
              </div>
              {hasSelection && (
                <div className="flex gap-2 overflow-x-auto pb-2 mb-5">
                  {job.selectionProcess.map((stage, i) => (
                    <div key={i} className={cn('flex-shrink-0 rounded-lg border px-4 py-3 text-center min-w-28',
                      i === 0 ? 'border-[#6C3EF4]/30 bg-[#6C3EF4]/10' : 'border-border-subtle bg-surface-elevated')}>
                      <div className={cn('text-xs font-bold mb-0.5', i === 0 ? 'text-[#6C3EF4]' : 'text-text-muted')}>Stage {i + 1}</div>
                      <div className="text-xs text-text-secondary leading-snug">{stage}</div>
                    </div>
                  ))}
                </div>
              )}
              <div className="space-y-3">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide">Preparation Timeline</p>
                {[
                  { phase: 'Now → Week 4', task: 'Cover syllabus basics — all subjects', color: 'bg-brand-blue' },
                  { phase: 'Week 5 → Week 8', task: 'Practice mock tests and previous year papers', color: 'bg-[#6C3EF4]' },
                  { phase: 'Week 9 → Week 11', task: 'Revise weak areas and current affairs', color: 'bg-success' },
                  { phase: 'Week 12', task: 'Final revision and exam day preparation', color: 'bg-warning' },
                ].map((row, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className={cn('w-2.5 h-2.5 rounded-full flex-shrink-0', row.color)} />
                    <span className="text-xs text-text-muted w-36 flex-shrink-0">{row.phase}</span>
                    <span className="text-xs text-text-secondary">{row.task}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-5">
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <div className="flex items-center gap-2 mb-3">
                  <GraduationCap className="w-4 h-4 text-success" />
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wide">Key Subjects</p>
                </div>
                <ul className="space-y-2">
                  {['General Intelligence & Reasoning', 'General Awareness & Current Affairs', 'Quantitative Aptitude', 'English Language', 'Subject-Specific Technical Paper'].map((sub) => (
                    <li key={sub} className="flex items-center gap-2 text-xs text-text-secondary">
                      <Star className="w-3 h-3 text-warning flex-shrink-0" /> {sub}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <div className="flex items-center gap-2 mb-3">
                  <CalendarDays className="w-4 h-4 text-brand-blue" />
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wide">Upcoming Milestones</p>
                </div>
                <ul className="space-y-3">
                  {[
                    { label: 'Complete first syllabus pass', date: 'In 4 weeks' },
                    { label: 'First full mock test', date: 'In 6 weeks' },
                    { label: 'Admit card download', date: job.examDate ? 'Before exam' : 'TBA' },
                    { label: 'Exam day', date: job.examDate ?? 'TBA' },
                  ].map((m) => (
                    <li key={m.label} className="flex items-center justify-between text-xs">
                      <span className="text-text-secondary">{m.label}</span>
                      <span className="text-text-muted font-medium">{m.date}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Recommended Weekly Plan</p>
              <div className="grid grid-cols-7 gap-1">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => (
                  <div key={day} className="rounded-lg bg-surface-elevated border border-border-subtle p-2 text-center">
                    <p className="text-[10px] font-bold text-text-muted mb-1">{day}</p>
                    <p className="text-[9px] text-text-secondary leading-tight">
                      {['Reasoning', 'GK + CA', 'Maths', 'English', 'Tech Paper', 'Mock Test', 'Revision'][i]}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Study Checklist */}
        {activeTab === 'study' && (
          <div className="max-w-2xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Study Checklist</h3>
              <ul className="space-y-2">
                {[
                  { task: 'Download official syllabus PDF', done: true },
                  { task: 'Collect previous year question papers (5 years)', done: true },
                  { task: 'Complete Reasoning module', done: false },
                  { task: 'Complete General Awareness module', done: false },
                  { task: 'Complete Quantitative Aptitude module', done: false },
                  { task: 'Complete subject-specific technical topics', done: false },
                  { task: 'Attempt 5 full mock tests', done: false },
                  { task: 'Revise weak chapters twice', done: false },
                  { task: 'Download admit card', done: false },
                ].map((item, i) => (
                  <li key={i} className={cn('flex items-center gap-3 px-3 py-2.5 rounded-lg border text-sm',
                    item.done ? 'border-success/20 bg-success/5 text-text-muted' : 'border-border-subtle bg-surface-elevated text-text-secondary')}>
                    {item.done ? <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" /> : <div className="w-4 h-4 rounded-full border-2 border-border-subtle flex-shrink-0" />}
                    <span className={item.done ? 'line-through' : ''}>{item.task}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Source History */}
        {activeTab === 'source' && (
          <div className="max-w-2xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Source History</h3>
              <div className="space-y-3">
                {[
                  { event: 'Notification published on official board website', source: 'Official Board Portal' },
                  { event: 'Detected and ingested by OPPORTA', source: 'Automated scan' },
                  { event: 'AI match analysis completed', source: 'AI Engine' },
                ].map((h, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <div className="flex flex-col items-center">
                      <div className="w-2 h-2 rounded-full bg-[#6C3EF4] mt-1.5" />
                      {i < 2 && <div className="w-px flex-1 bg-border-subtle mt-1" />}
                    </div>
                    <div className="pb-3">
                      <p className="text-text-primary font-medium">{h.event}</p>
                      <p className="text-xs text-text-muted mt-0.5">{h.source}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
