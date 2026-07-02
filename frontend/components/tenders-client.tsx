'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Search, Filter, MapPin, Clock, FileEdit, Eye, SlidersHorizontal, X,
  Sparkles, Bookmark, BookmarkCheck, Share2, FileText, RotateCcw, ChevronLeft, ChevronRight,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageHero } from '@/components/page-hero'
import { PageTabs } from '@/components/page-tabs'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { TenderAnalysisDialog } from '@/components/tender-analysis-dialog'
import { useToast } from '@/components/ui/toast'
import { useSaved } from '@/lib/saved-context'
import { useLanguage } from '@/lib/language-context'
import { TENDER_CATEGORIES, getDistricts } from '@/lib/mock-data'
import type { TenderMode, State, Tender } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

const modes: Array<TenderMode | 'All'> = ['All', 'Online', 'Offline', 'Newspaper']
const states: Array<State | 'All'> = ['All', 'Chhattisgarh', 'Uttar Pradesh']
const categories = [...TENDER_CATEGORIES]

export interface TendersClientProps {
  tenders: Tender[]
  total: number
  page: number
  pageSize: number
  q: string
  state: string
  category: string
  mode: string
  district: string
}

export function TendersClient({ tenders, total, page, pageSize, q, state, category, mode, district }: TendersClientProps) {
  const router = useRouter()
  const { toast } = useToast()
  const { isSaved, toggleSaved } = useSaved()
  const { t: tr } = useLanguage()
  const [showFilters, setShowFilters] = useState(state !== 'All' || category !== 'All' || mode !== 'All' || district !== 'All')
  const [searchInput, setSearchInput] = useState(q)
  const [analysisTender, setAnalysisTender] = useState<Tender | null>(null)

  // Build a /tenders URL, resetting to page 1 on any filter change.
  const buildUrl = (next: Partial<{ q: string; state: string; category: string; mode: string; district: string; page: number }>) => {
    const p = new URLSearchParams()
    const v = { q, state, category, mode, district, page, ...next }
    if (v.q) p.set('q', v.q)
    if (v.state && v.state !== 'All') p.set('state', v.state)
    if (v.category && v.category !== 'All') p.set('category', v.category)
    if (v.mode && v.mode !== 'All') p.set('mode', v.mode)
    if (v.district && v.district !== 'All') p.set('district', v.district)
    if (v.page && v.page > 1) p.set('page', String(v.page))
    const qs = p.toString()
    return qs ? `/tenders?${qs}` : '/tenders'
  }
  const go = (next: Parameters<typeof buildUrl>[0]) => router.push(buildUrl({ page: 1, ...next }))

  const hasActiveFilters = q !== '' || state !== 'All' || mode !== 'All' || district !== 'All' || category !== 'All'
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const fromN = total === 0 ? 0 : (page - 1) * pageSize + 1
  const toN = Math.min(page * pageSize, total)

  const toggleSave = async (t: Tender) => {
    const nowSaved = await toggleSaved(t)
    if (nowSaved) toast('Saved', 'success', { description: t.title })
    else toast('Removed from saved', 'info')
  }

  const share = async (title: string, path: string) => {
    const url = window.location.origin + path
    try {
      if (navigator.share) await navigator.share({ title, url })
      else if (navigator.clipboard) { await navigator.clipboard.writeText(url); toast('Link copied', 'success', { description: url }) }
    } catch { /* dismissed */ }
  }

  return (
    <AppShell pageTitle="Tenders" pageSubtitle={`${total.toLocaleString()} active tenders across CG & UP`} bg="tenders">
      <PageHero
        variant="tenders"
        eyebrow={tr('tender_portal')}
        icon={<FileText className="h-3.5 w-3.5" />}
        title={tr('government_tenders')}
        subtitle={`${total.toLocaleString()} active tenders across Chhattisgarh & Uttar Pradesh — search and filter across the full database.`}
      />
      <PageTabs
        accent="blue"
        tabs={[
          { label: tr('tender_portal'), href: '/tenders' },
          { label: tr('bid_documents'), href: '/bid-documents' },
        ]}
      />

      {/* Search (server-side) + Filter toggle */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <form onSubmit={(e) => { e.preventDefault(); go({ q: searchInput.trim() }) }} className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder={tr('search_tenders')}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-9 pr-9 py-2.5 rounded-lg border border-border-subtle bg-surface text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
          />
          {searchInput && (
            <button type="button" onClick={() => { setSearchInput(''); go({ q: '' }) }} className="absolute right-3 top-1/2 -translate-y-1/2">
              <X className="w-3.5 h-3.5 text-text-muted" />
            </button>
          )}
        </form>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={cn('flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors',
            showFilters ? 'border-brand-blue text-brand-blue bg-brand-blue/10' : 'border-border-subtle text-text-secondary bg-surface hover:bg-surface-elevated')}
        >
          <SlidersHorizontal className="w-4 h-4" /> {tr('filters')}
        </button>
      </div>

      {showFilters && (
        <div className="mb-5 p-4 rounded-xl border border-border-subtle bg-surface flex flex-wrap gap-4">
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">State</p>
            <div className="flex gap-1.5 flex-wrap">
              {states.map((s) => (
                <button key={s} onClick={() => go({ state: s, district: 'All' })}
                  className={cn('px-3 py-1 rounded-md text-xs font-medium border transition-colors',
                    state === s ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">District</p>
            <select value={district} onChange={(e) => go({ district: e.target.value })} disabled={state === 'All'} aria-label="Filter by district"
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-brand-blue disabled:opacity-50 disabled:cursor-not-allowed min-w-[150px]">
              <option value="All">All Districts</option>
              {getDistricts(state as State | 'All').map((d) => (<option key={d} value={d}>{d}</option>))}
            </select>
            {state === 'All' && <p className="text-[10px] text-text-muted mt-1">Select a state first</p>}
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">Mode</p>
            <div className="flex gap-1.5 flex-wrap">
              {modes.map((m) => (
                <button key={m} onClick={() => go({ mode: m })}
                  className={cn('px-3 py-1 rounded-md text-xs font-medium border transition-colors',
                    mode === m ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30' : 'bg-surface-elevated text-text-secondary border-border-subtle hover:text-text-primary')}>
                  {m}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">Category</p>
            <select value={category} onChange={(e) => go({ category: e.target.value })} aria-label="Filter by category"
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-brand-blue min-w-[170px]">
              {categories.map((c) => (<option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>))}
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={() => { setSearchInput(''); router.push('/tenders') }} disabled={!hasActiveFilters}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              <RotateCcw className="w-3.5 h-3.5" /> {tr('reset_filters')}
            </button>
          </div>
        </div>
      )}

      <p className="text-xs text-text-muted mb-4">
        {total === 0 ? tr('no_tenders_match') : `${tr('showing')} ${fromN.toLocaleString()}–${toN.toLocaleString()} ${tr('of')} ${total.toLocaleString()} ${tr('tenders').toLowerCase()}`}
      </p>

      <div className="grid gap-4">
        {tenders.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <Filter className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">{hasActiveFilters ? tr('no_tenders_match') : tr('no_tenders_available')}</p>
            <p className="text-sm text-text-muted mt-1">{tr('try_adjusting')}</p>
          </div>
        ) : (
          tenders.map((t) => (
            <div key={t.id} className="rounded-2xl card-premium hover-lift overflow-hidden group">
              <div className="p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <BadgeMode mode={t.mode} />
                      <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{t.category}</span>
                      {t.isRecommended && (<span className="text-[11px] font-semibold text-[#6C3EF4] bg-[#6C3EF4]/10 border border-[#6C3EF4]/20 px-2 py-0.5 rounded">Recommended</span>)}
                    </div>
                    <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{t.title}</h3>
                    <p className="text-xs text-text-muted mt-1">{t.nitNumber}</p>
                  </div>
                  <AiMatchBadge score={t.aiMatchScore} className="flex-shrink-0 mt-1" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-2 mb-4">
                  <div><p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Department</p><p className="text-xs text-text-secondary line-clamp-1">{t.department}</p></div>
                  <div><p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Location</p><p className="text-xs text-text-secondary flex items-center gap-1"><MapPin className="w-3 h-3" />{t.district}, {t.state === 'Chhattisgarh' ? 'CG' : 'UP'}</p></div>
                  <div><p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">Est. Value</p><p className="text-xs text-text-primary font-semibold">{t.estimatedValue}</p></div>
                  <div><p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">EMD</p><p className="text-xs text-text-secondary">{t.emd}</p></div>
                </div>
                <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                  <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {t.deadline}</span></span>
                  <span className="flex items-center gap-1 text-text-muted">Source: {t.source}</span>
                </div>
                <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
                  <Link href={`/tenders/${t.id}`}>
                    <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs h-8 gap-1.5"><Eye className="w-3.5 h-3.5" /> {tr('view_details')}</Button>
                  </Link>
                  <Button size="sm" variant="outline" onClick={() => setAnalysisTender(t)} title="Analyze" aria-label="Analyze"
                    className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" /><span className="hidden sm:inline">{tr('analyze')}</span>
                  </Button>
                  <Link href={`/bid-documents?tenderId=${t.id}`}>
                    <Button size="sm" variant="outline" title="Bid Document" aria-label="Bid Document"
                      className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                      <FileEdit className="w-3.5 h-3.5" /><span className="hidden sm:inline">{tr('bid_document')}</span>
                    </Button>
                  </Link>
                  <Button size="sm" variant="outline" onClick={() => toggleSave(t)} aria-pressed={isSaved(t.id)}
                    title={isSaved(t.id) ? 'Saved' : 'Save'} aria-label={isSaved(t.id) ? 'Saved' : 'Save'}
                    className={cn('text-xs h-8 gap-1.5', isSaved(t.id) ? 'border-brand-blue/40 text-brand-blue bg-brand-blue/10' : 'border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated')}>
                    {isSaved(t.id) ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                    <span className="hidden sm:inline">{isSaved(t.id) ? tr('saved') : tr('save')}</span>
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => share(t.title, `/tenders/${t.id}`)} title="Share" aria-label="Share"
                    className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                    <Share2 className="w-3.5 h-3.5" /><span className="hidden sm:inline">{tr('share')}</span>
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <Link href={buildUrl({ page: Math.max(1, page - 1) })} aria-disabled={page <= 1}
            className={cn('inline-flex items-center gap-1 rounded-lg border border-border-subtle px-3 py-2 text-xs font-semibold transition-colors',
              page <= 1 ? 'pointer-events-none opacity-40 text-text-muted' : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated')}>
            <ChevronLeft className="w-3.5 h-3.5" /> Prev
          </Link>
          <span className="text-xs text-text-muted">Page {page} of {totalPages}</span>
          <Link href={buildUrl({ page: Math.min(totalPages, page + 1) })} aria-disabled={page >= totalPages}
            className={cn('inline-flex items-center gap-1 rounded-lg border border-border-subtle px-3 py-2 text-xs font-semibold transition-colors',
              page >= totalPages ? 'pointer-events-none opacity-40 text-text-muted' : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated')}>
            Next <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      <TenderAnalysisDialog tender={analysisTender} open={analysisTender !== null} onClose={() => setAnalysisTender(null)} />
    </AppShell>
  )
}
