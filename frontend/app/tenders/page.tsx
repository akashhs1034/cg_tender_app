'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Search, Filter, MapPin, Clock, FileEdit, Eye, SlidersHorizontal, X,
  Sparkles, Bookmark, BookmarkCheck, Share2,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageTabs } from '@/components/page-tabs'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { tenders, TENDER_CATEGORIES, getDistricts } from '@/lib/mock-data'
import type { TenderMode, State } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const modes: Array<TenderMode | 'All'> = ['All', 'Online', 'Offline', 'Newspaper']
const states: Array<State | 'All'> = ['All', 'Chhattisgarh', 'Uttar Pradesh']
const categories = [...TENDER_CATEGORIES]

export default function TendersPage() {
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

  const filtered = tenders.filter((t) => {
    if (search && !t.title.toLowerCase().includes(search.toLowerCase()) && !t.department.toLowerCase().includes(search.toLowerCase())) return false
    if (modeFilter !== 'All' && t.mode !== modeFilter) return false
    if (stateFilter !== 'All' && t.state !== stateFilter) return false
    if (districtFilter !== 'All' && t.district !== districtFilter) return false
    if (catFilter !== 'All' && t.category !== catFilter) return false
    return true
  })

  return (
    <AppShell pageTitle="Tenders" pageSubtitle={`${tenders.length} active tenders across CG & UP`} bg="tenders">
      <PageTabs
        accent="blue"
        tabs={[
          { label: 'Tender Portal', href: '/tenders' },
          { label: 'Bid Documents', href: '/bid-documents' },
        ]}
      />
      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search tenders, departments..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
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
              ? 'border-brand-blue text-brand-blue bg-brand-blue/10'
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
                    stateFilter === s ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
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
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-brand-blue disabled:opacity-50 disabled:cursor-not-allowed min-w-[150px]"
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
                    modeFilter === m ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
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
                    catFilter === c ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Results count */}
      <p className="text-xs text-text-muted mb-4">Showing {filtered.length} of {tenders.length} tenders</p>

      {/* Tender cards */}
      <div className="grid gap-4">
        {filtered.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <Filter className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">No tenders match your filters</p>
            <p className="text-sm text-text-muted mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          filtered.map((t) => (
            <div key={t.id} className="rounded-2xl border border-border-subtle bg-surface hover:border-brand-blue/25 transition-all duration-200 overflow-hidden group">
              <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <BadgeMode mode={t.mode} />
                      <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{t.category}</span>
                      {t.isRecommended && (
                        <span className="text-[11px] font-semibold text-[#6C3EF4] bg-[#6C3EF4]/10 border border-[#6C3EF4]/20 px-2 py-0.5 rounded">Recommended</span>
                      )}
                    </div>
                    <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{t.title}</h3>
                    <p className="text-xs text-text-muted mt-1">{t.nitNumber}</p>
                  </div>
                  <AiMatchBadge score={t.aiMatchScore} className="flex-shrink-0 mt-1" />
                </div>

                {/* Meta grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-2 mb-4">
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Department</p>
                    <p className="text-xs text-text-secondary line-clamp-1">{t.department}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Location</p>
                    <p className="text-xs text-text-secondary flex items-center gap-1"><MapPin className="w-3 h-3" />{t.district}, {t.state === 'Chhattisgarh' ? 'CG' : 'UP'}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Est. Value</p>
                    <p className="text-xs text-text-primary font-semibold flex items-center gap-0.5">{t.estimatedValue}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">EMD</p>
                    <p className="text-xs text-text-secondary">{t.emd}</p>
                  </div>
                </div>

                {/* Deadline + Source */}
                <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                  <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {t.deadline}</span></span>
                  <span className="flex items-center gap-1 text-text-muted">Source: {t.source}</span>
                </div>

                {/* Actions — full labels on sm+, icon-only secondaries on mobile for a clean row */}
                <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
                  <Link href={`/tenders/${t.id}`}>
                    <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs h-8 gap-1.5">
                      <Eye className="w-3.5 h-3.5" /> View Details
                    </Button>
                  </Link>
                  <Link href={`/tenders/${t.id}`}>
                    <Button size="sm" variant="outline" title="Analyze" aria-label="Analyze"
                      className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" /><span className="hidden sm:inline">Analyze</span>
                    </Button>
                  </Link>
                  <Link href="/bid-documents">
                    <Button size="sm" variant="outline" title="Bid Document" aria-label="Bid Document"
                      className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                      <FileEdit className="w-3.5 h-3.5" /><span className="hidden sm:inline">Bid Document</span>
                    </Button>
                  </Link>
                  <Button size="sm" variant="outline" onClick={() => toggleSave(t.id)} aria-pressed={saved.has(t.id)}
                    title={saved.has(t.id) ? 'Saved' : 'Save'} aria-label={saved.has(t.id) ? 'Saved' : 'Save'}
                    className={cn('text-xs h-8 gap-1.5', saved.has(t.id)
                      ? 'border-brand-blue/40 text-brand-blue bg-brand-blue/10'
                      : 'border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated')}>
                    {saved.has(t.id) ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                    <span className="hidden sm:inline">{saved.has(t.id) ? 'Saved' : 'Save'}</span>
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => share(t.title, `/tenders/${t.id}`)} title="Share" aria-label="Share"
                    className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                    <Share2 className="w-3.5 h-3.5" /><span className="hidden sm:inline">Share</span>
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
