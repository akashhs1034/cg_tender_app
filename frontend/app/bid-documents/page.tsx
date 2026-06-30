'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Search, X, MapPin, Clock, FileEdit, FileText, ClipboardCheck,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageTabs } from '@/components/page-tabs'
import { BadgeMode } from '@/components/ui/badge-mode'
import { Button } from '@/components/ui/button'
import { tenders, TENDER_CATEGORIES, getDistricts } from '@/lib/mock-data'
import type { State } from '@/lib/mock-data'
import { cn } from '@/lib/utils'

const states: Array<State | 'All'> = ['All', 'Chhattisgarh', 'Uttar Pradesh']
const categories = [...TENDER_CATEGORIES]

export default function BidDocumentsPage() {
  // Tender selector filters — State + District are both always present here.
  const [search, setSearch] = useState('')
  const [stateFilter, setStateFilter] = useState<State | 'All'>('All')
  const [districtFilter, setDistrictFilter] = useState('All')
  const [catFilter, setCatFilter] = useState('All')

  const q = search.trim().toLowerCase()
  const filtered = tenders.filter((t) => {
    if (q && !t.nitNumber.toLowerCase().includes(q) && !t.title.toLowerCase().includes(q)) return false
    if (stateFilter !== 'All' && t.state !== stateFilter) return false
    if (districtFilter !== 'All' && t.district !== districtFilter) return false
    if (catFilter !== 'All' && t.category !== catFilter) return false
    return true
  })

  return (
    <AppShell pageTitle="Bid Documents" pageSubtitle="Prepare and track bid paperwork for any tender" bg="tenders">
      <PageTabs
        accent="blue"
        tabs={[
          { label: 'Tender Portal', href: '/tenders' },
          { label: 'Bid Documents', href: '/bid-documents' },
        ]}
      />

      {/* Tender selector / filter area */}
      <div className="mb-5 p-4 rounded-xl border border-border-subtle bg-surface">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search by Tender / NIT number…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
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
            {stateFilter === 'All' && <p className="text-[10px] text-text-muted mt-1">Select a state first</p>}
          </div>
          <div>
            <p className="text-xs text-text-muted mb-2 font-medium">Tender Category</p>
            <select
              value={catFilter}
              onChange={(e) => setCatFilter(e.target.value)}
              aria-label="Filter by tender category"
              className="px-3 py-1.5 rounded-md text-xs font-medium border border-border-subtle bg-surface-elevated text-text-secondary focus:outline-none focus:border-brand-blue min-w-[170px]"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <p className="text-xs text-text-muted mb-4">Showing {filtered.length} of {tenders.length} tenders</p>

      {/* Bid workspace cards */}
      <div className="grid gap-4">
        {filtered.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <FileText className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">No tenders match your selection</p>
            <p className="text-sm text-text-muted mt-1">Adjust the state, district, category, or NIT search</p>
          </div>
        ) : (
          filtered.map((t) => (
            <div key={t.id} className="rounded-2xl border border-border-subtle bg-surface p-5 hover:border-brand-blue/25 transition-colors">
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <BadgeMode mode={t.mode} />
                <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{t.category}</span>
              </div>
              <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{t.title}</h3>
              <p className="text-xs text-text-muted mt-1">{t.nitNumber}</p>

              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-text-secondary">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{t.district}, {t.state}</span>
                <span className="truncate max-w-[260px]">{t.department}</span>
                <span className="flex items-center gap-1 text-danger font-medium"><Clock className="w-3 h-3" />Deadline: {t.deadline}</span>
              </div>

              {/* Bid readiness */}
              <div className="mt-4">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wide">Bid Readiness</span>
                  <span className={cn('text-xs font-bold', t.bidReadiness >= 80 ? 'text-success' : t.bidReadiness >= 60 ? 'text-warning' : 'text-danger')}>{t.bidReadiness}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-surface-elevated overflow-hidden">
                  <div className={cn('h-full rounded-full', t.bidReadiness >= 80 ? 'bg-success' : t.bidReadiness >= 60 ? 'bg-warning' : 'bg-danger')}
                    style={{ width: `${t.bidReadiness}%` }} />
                </div>
                {t.missingDocuments.length > 0 && (
                  <p className="text-[11px] text-warning mt-1.5">{t.missingDocuments.length} document(s) still needed</p>
                )}
              </div>

              <div className="flex flex-wrap gap-2 pt-4 mt-4 border-t border-border-subtle">
                <Link href={`/tenders/${t.id}`}>
                  <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                    <FileText className="w-3.5 h-3.5" /> View Tender
                  </Button>
                </Link>
                <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs h-8 gap-1.5">
                  <FileEdit className="w-3.5 h-3.5" /> Generate Draft Bid
                </Button>
                <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                  <ClipboardCheck className="w-3.5 h-3.5" /> Bid Checklist
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </AppShell>
  )
}
