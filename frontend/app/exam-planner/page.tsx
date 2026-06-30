'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Search, X, MapPin, CalendarClock, Users, GraduationCap, BookOpen,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageTabs } from '@/components/page-tabs'
import { BadgeMode } from '@/components/ui/badge-mode'
import { Button } from '@/components/ui/button'
import { jobs, JOB_CATEGORIES, getDistricts } from '@/lib/mock-data'
import type { State } from '@/lib/mock-data'
import { cn } from '@/lib/utils'

const states: Array<State | 'All'> = ['All', 'Chhattisgarh', 'Uttar Pradesh']
const categories = [...JOB_CATEGORIES]

export default function ExamPlannerPage() {
  // Job selector filters — State + District are both always present here.
  const [search, setSearch] = useState('')
  const [stateFilter, setStateFilter] = useState<State | 'All'>('All')
  const [districtFilter, setDistrictFilter] = useState('All')
  const [catFilter, setCatFilter] = useState('All')

  const q = search.trim().toLowerCase()
  const filtered = jobs.filter((j) => {
    if (q && !j.advNumber.toLowerCase().includes(q) && !j.title.toLowerCase().includes(q)) return false
    if (stateFilter !== 'All' && j.state !== stateFilter) return false
    if (districtFilter !== 'All' && j.district !== districtFilter) return false
    if (catFilter !== 'All' && j.category !== catFilter) return false
    return true
  })

  return (
    <AppShell pageTitle="Exam Planner" pageSubtitle="Plan your preparation for upcoming government exams" bg="jobs">
      <PageTabs
        accent="purple"
        tabs={[
          { label: 'Government Jobs', href: '/jobs' },
          { label: 'Exam Planner', href: '/exam-planner' },
        ]}
      />

      {/* Job selector / filter area */}
      <div className="mb-5 p-4 rounded-xl border border-border-subtle bg-surface">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search by Advertisement number…"
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
            {stateFilter === 'All' && <p className="text-[10px] text-text-muted mt-1">Select a state first</p>}
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">Job Category</p>
            <select
              value={catFilter}
              onChange={(e) => setCatFilter(e.target.value)}
              aria-label="Filter by job category"
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-[#6C3EF4] min-w-[170px]"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <p className="text-xs text-text-muted mb-4">Showing {filtered.length} of {jobs.length} notifications</p>

      {/* Exam plan cards */}
      <div className="grid gap-4">
        {filtered.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <GraduationCap className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">No notifications match your selection</p>
            <p className="text-sm text-text-muted mt-1">Adjust the state, district, category, or advertisement search</p>
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
                <span className="flex items-center gap-1"><Users className="w-3 h-3 text-[#6C3EF4]" />{j.vacancies.toLocaleString()} posts</span>
                <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />{j.qualification}</span>
              </div>

              {/* Exam timeline */}
              <div className="mt-4 flex flex-wrap gap-3">
                <div className="flex-1 min-w-[150px] rounded-lg border border-[#6C3EF4]/20 bg-[#6C3EF4]/5 px-3 py-2.5">
                  <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide">Exam Date</p>
                  <p className="text-sm font-semibold text-text-primary flex items-center gap-1.5 mt-0.5">
                    <CalendarClock className="w-3.5 h-3.5 text-[#6C3EF4]" />{j.examDate ?? 'To be announced'}
                  </p>
                </div>
                <div className="flex-1 min-w-[150px] rounded-lg border border-border-subtle bg-surface-elevated px-3 py-2.5">
                  <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide">Apply Before</p>
                  <p className="text-sm font-semibold text-danger mt-0.5">{j.deadline}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-4 mt-4 border-t border-border-subtle">
                <Link href={`/jobs/${j.id}`}>
                  <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                    <BookOpen className="w-3.5 h-3.5" /> View Job
                  </Button>
                </Link>
                <Button size="sm" className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white font-semibold text-xs h-8 gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5" /> Build Study Plan
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </AppShell>
  )
}
