'use client'

import { useState } from 'react'
import {
  FileText, Newspaper, MapPin, Clock, BarChart2, Activity,
  Target, ArrowUpRight, Briefcase, Globe, RefreshCw, Layers,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import type { Analytics, CategorySlice } from '@/lib/data'
import { cn } from '@/lib/utils'

const SLICE_COLORS = ['#3B7CF4', '#6C3EF4', '#22D3EE', '#10B981', '#F59E0B', '#EF4444', '#64748B']

const tabs = ['Overview', 'Tenders', 'Jobs', 'Sources'] as const
type Tab = typeof tabs[number]

function BarList({ slices, unit }: { slices: CategorySlice[]; unit?: string }) {
  if (slices.length === 0) return <p className="text-xs text-text-muted">No data available.</p>
  return (
    <div className="space-y-3">
      {slices.map((c, i) => (
        <div key={c.label}>
          <div className="flex items-center justify-between mb-1 gap-3">
            <span className="text-xs text-text-secondary truncate">{c.label}</span>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className="text-xs text-text-muted">{c.count.toLocaleString()}{unit ? ` ${unit}` : ''}</span>
              <span className="text-xs font-semibold text-text-primary w-8 text-right">{c.pct}%</span>
            </div>
          </div>
          <div className="h-1.5 rounded-full bg-surface-elevated overflow-hidden">
            <div className="h-full rounded-full transition-all" style={{ width: `${c.pct}%`, backgroundColor: SLICE_COLORS[i % SLICE_COLORS.length] }} />
          </div>
        </div>
      ))}
    </div>
  )
}

export function AnalyticsClient({ analytics: a }: { analytics: Analytics }) {
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const totalStates = a.cgCount + a.upCount || 1
  const totalModes = a.modes.online + a.modes.offline + a.modes.newspaper || 1

  const kpiCards = [
    { label: 'Total Opportunities', value: a.totalOpportunities.toLocaleString(), sub: 'Tenders + jobs in database', icon: Target, iconColor: 'text-brand-blue', iconBg: 'bg-brand-blue/10' },
    { label: 'Total Vacancies', value: a.totalVacancies.toLocaleString(), sub: 'Across all job postings', icon: Briefcase, iconColor: 'text-[#6C3EF4]', iconBg: 'bg-[#6C3EF4]/10' },
    { label: 'Avg AI Match Score', value: `${a.avgScore}%`, sub: 'Across scored opportunities', icon: BarChart2, iconColor: 'text-success', iconBg: 'bg-success/10' },
    { label: 'Expiring Soon', value: a.expiringSoon.toLocaleString(), sub: 'Tenders closing within 7 days', icon: Clock, iconColor: 'text-danger', iconBg: 'bg-danger/10' },
  ]

  const modeCards = [
    { label: 'Online Portal', icon: Activity, count: a.modes.online, color: '#3B7CF4', iconBg: 'bg-brand-blue/10', iconColor: 'text-brand-blue' },
    { label: 'Newspaper', icon: Newspaper, count: a.modes.newspaper, color: '#22D3EE', iconBg: 'bg-brand-cyan/10', iconColor: 'text-brand-cyan' },
    { label: 'Offline / District', icon: FileText, count: a.modes.offline, color: '#10B981', iconBg: 'bg-success/10', iconColor: 'text-success' },
  ]

  return (
    <AppShell pageTitle="Analytics" pageSubtitle="Platform-wide opportunity intelligence">
      {/* Tab bar */}
      <div className="flex gap-1 p-1 rounded-xl bg-surface border border-border-subtle w-fit mb-7">
        {tabs.map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={cn('px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-150',
              activeTab === tab ? 'bg-brand-blue text-white' : 'text-text-secondary hover:text-text-primary')}>
            {tab}
          </button>
        ))}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-7">
        {kpiCards.map((k) => (
          <div key={k.label} className="rounded-xl border border-border-subtle bg-surface p-5">
            <div className="flex items-center justify-between mb-3">
              <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center', k.iconBg)}>
                <k.icon className={cn('w-4 h-4', k.iconColor)} />
              </div>
              <ArrowUpRight className="w-4 h-4 text-text-muted" />
            </div>
            <p className="font-heading font-bold text-2xl text-text-primary">{k.value}</p>
            <p className="text-xs font-medium text-text-secondary mt-0.5">{k.label}</p>
            <p className="text-[11px] text-text-muted mt-0.5">{k.sub}</p>
          </div>
        ))}
      </div>

      {activeTab === 'Overview' && (
        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* State split */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Tender State Distribution</h2>
              <div className="space-y-4">
                {[
                  { label: 'Chhattisgarh', count: a.cgCount, color: '#3B7CF4' },
                  { label: 'Uttar Pradesh', count: a.upCount, color: '#6C3EF4' },
                ].map((s) => {
                  const pct = Math.round((s.count / totalStates) * 100)
                  return (
                    <div key={s.label}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <MapPin className="w-3.5 h-3.5" style={{ color: s.color }} />
                          <span className="text-sm text-text-secondary">{s.label}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-semibold text-text-primary">{s.count.toLocaleString()}</span>
                          <span className="text-xs text-text-muted w-8 text-right">{pct}%</span>
                        </div>
                      </div>
                      <div className="h-2 rounded-full bg-surface-elevated overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: s.color }} />
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="mt-5 pt-4 border-t border-border-subtle flex items-center justify-between">
                <span className="text-xs text-text-muted">Total tenders</span>
                <span className="text-sm font-bold text-text-primary font-heading">{a.totalTenders.toLocaleString()}</span>
              </div>
            </div>

            {/* Deadline urgency (real) */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Activity Snapshot</h2>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3">
                  <p className="font-heading font-bold text-2xl text-danger">{a.expiringSoon.toLocaleString()}</p>
                  <p className="text-xs text-text-secondary mt-0.5">Closing within 7 days</p>
                </div>
                <div className="rounded-xl border border-warning/20 bg-warning/10 px-4 py-3">
                  <p className="font-heading font-bold text-2xl text-warning">{a.corrigendums.toLocaleString()}</p>
                  <p className="text-xs text-text-secondary mt-0.5">Corrigendums issued</p>
                </div>
                <div className="rounded-xl border border-brand-blue/20 bg-brand-blue/10 px-4 py-3">
                  <p className="font-heading font-bold text-2xl text-brand-blue">{a.totalTenders.toLocaleString()}</p>
                  <p className="text-xs text-text-secondary mt-0.5">Active tenders</p>
                </div>
                <div className="rounded-xl border border-[#6C3EF4]/20 bg-[#6C3EF4]/10 px-4 py-3">
                  <p className="font-heading font-bold text-2xl text-[#6C3EF4]">{a.totalJobs.toLocaleString()}</p>
                  <p className="text-xs text-text-secondary mt-0.5">Active jobs</p>
                </div>
              </div>
            </div>
          </div>

          {/* Mode breakdown (real) */}
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Tender Source Modes</h2>
            <div className="grid grid-cols-3 gap-4">
              {modeCards.map((m) => {
                const pct = Math.round((m.count / totalModes) * 100)
                return (
                  <div key={m.label} className="rounded-xl border border-border-subtle bg-surface-elevated p-4">
                    <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center mb-3', m.iconBg)}>
                      <m.icon className={cn('w-4 h-4', m.iconColor)} />
                    </div>
                    <p className="font-heading font-bold text-xl text-text-primary">{m.count.toLocaleString()}</p>
                    <p className="text-xs text-text-secondary mt-0.5">{m.label}</p>
                    <div className="mt-2 h-1 rounded-full bg-background overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: m.color }} />
                    </div>
                    <p className="text-[10px] text-text-muted mt-1">{pct}% of tenders</p>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Tenders' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center gap-2 mb-5"><Layers className="w-4 h-4 text-brand-blue" /><h2 className="font-heading font-semibold text-sm text-text-primary">Tenders by Category</h2></div>
            <BarList slices={a.tenderCategories} />
          </div>
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center gap-2 mb-5"><Globe className="w-4 h-4 text-brand-cyan" /><h2 className="font-heading font-semibold text-sm text-text-primary">Tenders by Source Portal</h2></div>
            <BarList slices={a.sources} />
          </div>
        </div>
      )}

      {activeTab === 'Jobs' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center gap-2 mb-5"><Layers className="w-4 h-4 text-[#6C3EF4]" /><h2 className="font-heading font-semibold text-sm text-text-primary">Jobs by Category</h2></div>
            <BarList slices={a.jobCategories} />
          </div>
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Vacancy Summary</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">Total vacancies</span>
                <span className="text-lg font-bold font-heading text-text-primary">{a.totalVacancies.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">Active job postings</span>
                <span className="text-lg font-bold font-heading text-text-primary">{a.totalJobs.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">Avg AI match score</span>
                <span className="text-lg font-bold font-heading text-success">{a.avgScore}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Sources' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center gap-2 mb-5"><Globe className="w-4 h-4 text-brand-blue" /><h2 className="font-heading font-semibold text-sm text-text-primary">Top Source Portals</h2></div>
            <BarList slices={a.sources} />
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { label: 'Tenders Tracked', value: a.totalTenders.toLocaleString(), sub: 'Across all portals & newspapers', icon: FileText, color: 'text-brand-blue', bg: 'bg-brand-blue/10' },
              { label: 'Jobs Tracked', value: a.totalJobs.toLocaleString(), sub: 'Across boards & departments', icon: Briefcase, color: 'text-[#6C3EF4]', bg: 'bg-[#6C3EF4]/10' },
              { label: 'Corrigendums', value: a.corrigendums.toLocaleString(), sub: 'Tender amendments tracked', icon: RefreshCw, color: 'text-warning', bg: 'bg-warning/10' },
            ].map((s) => (
              <div key={s.label} className="rounded-xl border border-border-subtle bg-surface p-5">
                <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center mb-3', s.bg)}>
                  <s.icon className={cn('w-4 h-4', s.color)} />
                </div>
                <p className="font-heading font-bold text-xl text-text-primary">{s.value}</p>
                <p className="text-xs font-medium text-text-secondary mt-0.5">{s.label}</p>
                <p className="text-[11px] text-text-muted mt-0.5">{s.sub}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </AppShell>
  )
}
