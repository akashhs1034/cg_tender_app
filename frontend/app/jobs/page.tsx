'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Search, Filter, MapPin, Clock, Users, Eye, SlidersHorizontal, X, CheckCircle,
  GraduationCap, Bookmark, BookmarkCheck, Share2,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageTabs } from '@/components/page-tabs'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { jobs, JOB_CATEGORIES, getDistricts } from '@/lib/mock-data'
import type { TenderMode, State } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const modes: Array<TenderMode | 'All'> = ['All', 'Online', 'Offline', 'Newspaper']
const states: Array<State | 'All'> = ['All', 'Chhattisgarh', 'Uttar Pradesh']
const categories = [...JOB_CATEGORIES]

export default function JobsPage() {
  const [search, setSearch] = useState('')
  const [modeFilter, setModeFilter] = useState<TenderMode | 'All'>('All')
  const [stateFilter, setStateFilter] = useState<State | 'All'>('All')
  const [districtFilter, setDistrictFilter] = useState('All')
  const [catFilter, setCatFilter] = useState('All')
  const [showFilters, setShowFilters] = useState(false)
  const [saved, setSaved] = useState<Set<string>>(new Set())

  const toggleSave = (id: string) =>
    setSaved((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const share = async (title: string, path: string) => {
    const url = window.location.origin + path
    try {
      if (navigator.share) await navigator.share({ title, url })
      else await navigator.clipboard?.writeText(url)
    } catch {
      /* share sheet dismissed — ignore */
    }
  }

  const filtered = jobs.filter((j) => {
    if (search && !j.title.toLowerCase().includes(search.toLowerCase()) && !j.department.toLowerCase().includes(search.toLowerCase())) return false
    if (modeFilter !== 'All' && j.mode !== modeFilter) return false
    if (stateFilter !== 'All' && j.state !== stateFilter) return false
    if (districtFilter !== 'All' && j.district !== districtFilter) return false
    if (catFilter !== 'All' && j.category !== catFilter) return false
    return true
  })

  return (
    <AppShell pageTitle="Jobs" pageSubtitle={`${jobs.length} active jobs across CG & UP`} bg="jobs">
      <PageTabs
        accent="purple"
        tabs={[
          { label: 'Government Jobs', href: '/jobs' },
          { label: 'Exam Planner', href: '/exam-planner' },
        ]}
      />
      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search jobs, departments..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-[#6C3EF4] transition-colors"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2">
              <X className="w-3.5 h-3.5 text-text-muted" />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            'flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors',
            showFilters
              ? 'border-[#6C3EF4] text-[#6C3EF4] bg-[#6C3EF4]/10'
              : 'border-border-subtle text-text-secondary bg-surface hover:bg-surface-elevated'
          )}
        >
          <SlidersHorizontal className="w-4 h-4" /> Filters
        </button>
      </div>

      {/* Expanded filters */}
      {showFilters && (
        <div className="mb-5 p-4 rounded-xl border border-border-subtle bg-surface flex flex-wrap gap-4">
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">State</p>
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
            <p className="text-xs text-text-muted mb-2 font-medium">District</p>
            <select
              value={districtFilter}
              onChange={(e) => setDistrictFilter(e.target.value)}
              disabled={stateFilter === 'All'}
              aria-label="Filter by district"
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-[#6C3EF4] disabled:opacity-50 disabled:cursor-not-allowed min-w-[150px]"
            >
              <option value="All">All Districts</option>
              {getDistricts(stateFilter).map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            {stateFilter === 'All' && (
              <p className="text-[10px] text-text-muted mt-1">Select a state first</p>
            )}
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">Mode</p>
            <div className="flex gap-1.5 flex-wrap">
              {modes.map((m) => (
                <button key={m} onClick={() => setModeFilter(m)}
                  className={cn('px-3 py-1 rounded-md text-xs font-medium border transition-colors',
                    modeFilter === m ? 'bg-[#6C3EF4]/15 text-[#6C3EF4] border-[#6C3EF4]/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
                  {m}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">Category</p>
            <div className="flex gap-1.5 flex-wrap">
              {categories.map((c) => (
                <button key={c} onClick={() => setCatFilter(c)}
                  className={cn('px-3 py-1 rounded-md text-xs font-medium border transition-colors',
                    catFilter === c ? 'bg-[#6C3EF4]/15 text-[#6C3EF4] border-[#6C3EF4]/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <p className="text-xs text-text-muted mb-4">Showing {filtered.length} of {jobs.length} jobs</p>

      {/* Job cards */}
      <div className="grid gap-4">
        {filtered.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <Filter className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">No jobs match your filters</p>
            <p className="text-sm text-text-muted mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          filtered.map((j) => (
            <div key={j.id} className="rounded-2xl border border-border-subtle bg-surface hover:border-[#6C3EF4]/25 transition-all duration-200 overflow-hidden group">
              <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <BadgeMode mode={j.mode} />
                      <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{j.category}</span>
                      {j.isRecommended && (
                        <span className="text-[11px] font-semibold text-[#6C3EF4] bg-[#6C3EF4]/10 border border-[#6C3EF4]/20 px-2 py-0.5 rounded">Recommended</span>
                      )}
                    </div>
                    <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{j.title}</h3>
                    <p className="text-xs text-text-muted mt-1">{j.advNumber}</p>
                  </div>
                  <AiMatchBadge score={j.matchScore} className="flex-shrink-0 mt-1" />
                </div>

                {/* Meta grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-2 mb-4">
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Department</p>
                    <p className="text-xs text-text-secondary line-clamp-1">{j.department}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Location</p>
                    <p className="text-xs text-text-secondary flex items-center gap-1"><MapPin className="w-3 h-3" />{j.district}, {j.state === 'Chhattisgarh' ? 'CG' : 'UP'}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Vacancies</p>
                    <p className="text-xs text-text-primary font-semibold flex items-center gap-1"><Users className="w-3 h-3 text-[#6C3EF4]" />{j.vacancies.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Qualification</p>
                    <p className="text-xs text-text-secondary truncate">{j.qualification}</p>
                  </div>
                </div>

                {/* Salary + Deadline */}
                <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                  <span className="font-semibold text-text-primary">{j.salary}</span>
                  <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {j.deadline}</span></span>
                  {j.examDate && <span className="flex items-center gap-1 text-text-muted">Exam: {j.examDate}</span>}
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-2 pt-3 border-t border-border-subtle">
                  <Link href={`/jobs/${j.id}`}>
                    <Button size="sm" className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold text-xs h-8 gap-1.5">
                      <Eye className="w-3.5 h-3.5" /> View Details
                    </Button>
                  </Link>
                  <Link href={`/jobs/${j.id}`}>
                    <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                      <CheckCircle className="w-3.5 h-3.5" /> Check Eligibility
                    </Button>
                  </Link>
                  <Link href="/exam-planner">
                    <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                      <GraduationCap className="w-3.5 h-3.5" /> Exam Planner
                    </Button>
                  </Link>
                  <Button size="sm" variant="outline" onClick={() => toggleSave(j.id)} aria-pressed={saved.has(j.id)}
                    className={cn('text-xs h-8 gap-1.5', saved.has(j.id)
                      ? 'border-[#6C3EF4]/40 text-[#6C3EF4] bg-[#6C3EF4]/10'
                      : 'border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated')}>
                    {saved.has(j.id) ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                    {saved.has(j.id) ? 'Saved' : 'Save'}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => share(j.title, `/jobs/${j.id}`)}
                    className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                    <Share2 className="w-3.5 h-3.5" /> Share
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </AppShell>
  )
}
