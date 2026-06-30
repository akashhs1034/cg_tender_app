'use client'

import { useState } from 'react'
import {
  TrendingUp, TrendingDown, FileText, Briefcase, Newspaper,
  RefreshCw, MapPin, Clock, BarChart2, PieChart, Activity,
  Calendar, Target, ArrowUpRight, ArrowDownRight,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { tenders, jobs, dashboardStats } from '@/lib/mock-data'
import { cn } from '@/lib/utils'

// ── Derived analytics data ──────────────────────────────────────────────────

const tendersByCategory = [
  { label: 'Road & Highway', count: 1, value: '₹24.6 Cr', color: '#3B7CF4', pct: 22 },
  { label: 'Building Construction', count: 2, value: '₹5.95 Cr', color: '#22D3EE', pct: 18 },
  { label: 'Water & Sanitation', count: 1, value: '₹15.7 Cr', color: '#10B981', pct: 20 },
  { label: 'IT & Electronics', count: 1, value: '₹8.2 Cr', color: '#6C3EF4', pct: 17 },
  { label: 'Electrical & Solar', count: 1, value: '₹3.4 Cr', color: '#F59E0B', pct: 13 },
]

const jobsByCategory = [
  { label: 'Engineering', count: 2, pct: 26, color: '#3B7CF4' },
  { label: 'Police & Defence', count: 1, pct: 21, color: '#6C3EF4' },
  { label: 'Education', count: 1, pct: 20, color: '#10B981' },
  { label: 'Administrative', count: 1, pct: 18, color: '#22D3EE' },
  { label: 'Revenue & Admin', count: 1, pct: 15, color: '#F59E0B' },
]

const weeklyTrend = [
  { day: 'Mon', tenders: 28, jobs: 42 },
  { day: 'Tue', tenders: 35, jobs: 58 },
  { day: 'Wed', tenders: 22, jobs: 47 },
  { day: 'Thu', tenders: 41, jobs: 63 },
  { day: 'Fri', tenders: 38, jobs: 55 },
  { day: 'Sat', tenders: 19, jobs: 31 },
  { day: 'Sun', tenders: 12, jobs: 24 },
]

const maxBarValue = Math.max(...weeklyTrend.map((d) => Math.max(d.tenders, d.jobs)))

const sourceBreakdown = [
  { source: 'etender.cg.gov.in', type: 'Online', count: 1842, pct: 37, state: 'CG', color: '#3B7CF4' },
  { source: 'etender.up.gov.in', type: 'Online', count: 2104, pct: 42, state: 'UP', color: '#6C3EF4' },
  { source: 'Newspaper (CG)', type: 'Newspaper', count: 189, pct: 10, state: 'CG', color: '#22D3EE' },
  { source: 'Newspaper (UP)', type: 'Newspaper', count: 123, pct: 7, state: 'UP', color: '#10B981' },
  { source: 'District Offline', type: 'Offline', count: 43, pct: 4, state: 'Both', color: '#F59E0B' },
]

const deadlineSummary = [
  { label: 'Today', count: 4, color: 'text-danger', bg: 'bg-danger/10 border-danger/20' },
  { label: 'Next 3 days', count: 12, color: 'text-warning', bg: 'bg-warning/10 border-warning/20' },
  { label: 'Next 7 days', count: 29, color: 'text-brand-cyan', bg: 'bg-brand-cyan/10 border-brand-cyan/20' },
  { label: 'Next 30 days', count: 89, color: 'text-brand-blue', bg: 'bg-brand-blue/10 border-brand-blue/20' },
]

const kpiCards = [
  {
    label: 'Total Opportunities',
    value: (dashboardStats.activeTenders + dashboardStats.activeJobs).toLocaleString(),
    sub: 'Tenders + Jobs combined',
    icon: Target,
    iconColor: 'text-brand-blue',
    iconBg: 'bg-brand-blue/10',
    change: '+22',
    changeType: 'up' as const,
  },
  {
    label: 'New This Week',
    value: '234',
    sub: 'Across all sources',
    icon: Activity,
    iconColor: 'text-success',
    iconBg: 'bg-success/10',
    change: '+18%',
    changeType: 'up' as const,
  },
  {
    label: 'Avg AI Match Score',
    value: '76%',
    sub: 'Across your tracked items',
    icon: BarChart2,
    iconColor: 'text-[#6C3EF4]',
    iconBg: 'bg-[#6C3EF4]/10',
    change: '+4%',
    changeType: 'up' as const,
  },
  {
    label: 'Expiring Soon',
    value: dashboardStats.closingSoon.toString(),
    sub: 'Within next 7 days',
    icon: Clock,
    iconColor: 'text-danger',
    iconBg: 'bg-danger/10',
    change: '-3',
    changeType: 'down' as const,
  },
]

const tabs = ['Overview', 'Tenders', 'Jobs', 'Sources'] as const
type Tab = typeof tabs[number]

// ── Component ──────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('Overview')

  return (
    <AppShell pageTitle="Analytics" pageSubtitle="Platform-wide opportunity intelligence">
      {/* Tab bar */}
      <div className="flex gap-1 p-1 rounded-xl bg-surface border border-border-subtle w-fit mb-7">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-150',
              activeTab === tab
                ? 'bg-brand-blue text-white'
                : 'text-text-secondary hover:text-text-primary'
            )}
          >
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
                <k.icon className={cn('w-4.5 h-4.5', k.iconColor)} />
              </div>
              <span className={cn(
                'flex items-center gap-0.5 text-xs font-semibold',
                k.changeType === 'up' ? 'text-success' : 'text-danger'
              )}>
                {k.changeType === 'up' ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                {k.change}
              </span>
            </div>
            <p className="font-heading font-bold text-2xl text-text-primary">{k.value}</p>
            <p className="text-xs font-medium text-text-secondary mt-0.5">{k.label}</p>
            <p className="text-[11px] text-text-muted mt-0.5">{k.sub}</p>
          </div>
        ))}
      </div>

      {/* Overview Tab Content */}
      {activeTab === 'Overview' && (
        <div className="space-y-6">
          {/* Weekly trend bar chart */}
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="font-heading font-semibold text-sm text-text-primary">Weekly New Listings Trend</h2>
                <p className="text-xs text-text-muted mt-0.5">New tenders and jobs posted per day this week</p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5"><span className="w-3 h-2 rounded-sm bg-brand-blue inline-block" />Tenders</span>
                <span className="flex items-center gap-1.5 text-text-muted"><span className="w-3 h-2 rounded-sm bg-[#6C3EF4] inline-block" />Jobs</span>
              </div>
            </div>
            <div className="flex items-end gap-3 h-32">
              {weeklyTrend.map((d) => (
                <div key={d.day} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex items-end gap-0.5 h-24">
                    <div
                      className="flex-1 bg-brand-blue rounded-t-sm opacity-80 hover:opacity-100 transition-opacity"
                      style={{ height: `${(d.tenders / maxBarValue) * 100}%` }}
                      title={`${d.tenders} tenders`}
                    />
                    <div
                      className="flex-1 bg-[#6C3EF4] rounded-t-sm opacity-80 hover:opacity-100 transition-opacity"
                      style={{ height: `${(d.jobs / maxBarValue) * 100}%` }}
                      title={`${d.jobs} jobs`}
                    />
                  </div>
                  <span className="text-[10px] text-text-muted">{d.day}</span>
                </div>
              ))}
            </div>
          </div>

          {/* CG vs UP + Deadline split */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* State split */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">State Distribution</h2>
              <div className="space-y-4">
                {[
                  { label: 'Chhattisgarh', count: dashboardStats.cgCount, color: '#3B7CF4', icon: '🏛' },
                  { label: 'Uttar Pradesh', count: dashboardStats.upCount, color: '#6C3EF4', icon: '🏛' },
                ].map((s) => {
                  const total = dashboardStats.cgCount + dashboardStats.upCount
                  const pct = Math.round((s.count / total) * 100)
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
                <span className="text-xs text-text-muted">Total opportunities</span>
                <span className="text-sm font-bold text-text-primary font-heading">
                  {(dashboardStats.cgCount + dashboardStats.upCount).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Deadline urgency */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Deadline Urgency</h2>
              <div className="grid grid-cols-2 gap-3">
                {deadlineSummary.map((d) => (
                  <div key={d.label} className={cn('rounded-xl border px-4 py-3', d.bg)}>
                    <p className={cn('font-heading font-bold text-2xl', d.color)}>{d.count}</p>
                    <p className="text-xs text-text-secondary mt-0.5">{d.label}</p>
                  </div>
                ))}
              </div>
              <div className="mt-5 pt-4 border-t border-border-subtle">
                <p className="text-xs text-text-muted">
                  {dashboardStats.corrigendums} corrigendums issued this month — always check for updates before submitting.
                </p>
              </div>
            </div>
          </div>

          {/* Mode breakdown */}
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Opportunity Source Modes</h2>
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: 'Online Portal', icon: Activity, count: 3946, pct: 79, color: '#3B7CF4', iconBg: 'bg-brand-blue/10', iconColor: 'text-brand-blue' },
                { label: 'Newspaper', icon: Newspaper, count: 312, pct: 12, color: '#22D3EE', iconBg: 'bg-brand-cyan/10', iconColor: 'text-brand-cyan' },
                { label: 'Offline / District', icon: FileText, count: 143, pct: 9, color: '#10B981', iconBg: 'bg-success/10', iconColor: 'text-success' },
              ].map((m) => (
                <div key={m.label} className="rounded-xl border border-border-subtle bg-surface-elevated p-4">
                  <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center mb-3', m.iconBg)}>
                    <m.icon className={cn('w-4 h-4', m.iconColor)} />
                  </div>
                  <p className="font-heading font-bold text-xl text-text-primary">{m.count.toLocaleString()}</p>
                  <p className="text-xs text-text-secondary mt-0.5">{m.label}</p>
                  <div className="mt-2 h-1 rounded-full bg-background overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${m.pct}%`, backgroundColor: m.color }} />
                  </div>
                  <p className="text-[10px] text-text-muted mt-1">{m.pct}% of total</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tenders Tab */}
      {activeTab === 'Tenders' && (
        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Category breakdown */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Tenders by Category</h2>
              <div className="space-y-3">
                {tendersByCategory.map((c) => (
                  <div key={c.label}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-text-secondary">{c.label}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-text-muted">{c.value}</span>
                        <span className="text-xs font-semibold text-text-primary w-8 text-right">{c.pct}%</span>
                      </div>
                    </div>
                    <div className="h-1.5 rounded-full bg-surface-elevated overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${c.pct}%`, backgroundColor: c.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Bid readiness distribution */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Bid Readiness (Tracked Tenders)</h2>
              <div className="space-y-3">
                {tenders.map((t) => (
                  <div key={t.id} className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-text-secondary truncate">{t.title.substring(0, 40)}…</p>
                    </div>
                    <div className="w-24 flex items-center gap-2">
                      <div className="flex-1 h-1.5 rounded-full bg-surface-elevated overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${t.bidReadiness}%`,
                            backgroundColor: t.bidReadiness >= 80 ? '#10B981' : t.bidReadiness >= 60 ? '#F59E0B' : '#EF4444',
                          }}
                        />
                      </div>
                      <span className={cn(
                        'text-[11px] font-semibold w-7 text-right',
                        t.bidReadiness >= 80 ? 'text-success' : t.bidReadiness >= 60 ? 'text-warning' : 'text-danger'
                      )}>
                        {t.bidReadiness}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Risk analysis table */}
          <div className="rounded-2xl border border-border-subtle bg-surface overflow-hidden">
            <div className="px-6 py-4 border-b border-border-subtle">
              <h2 className="font-heading font-semibold text-sm text-text-primary">Risk Level Analysis</h2>
              <p className="text-xs text-text-muted mt-0.5">AI-assessed risk based on eligibility gaps and document readiness</p>
            </div>
            <div className="divide-y divide-border-subtle">
              {tenders.map((t) => (
                <div key={t.id} className="flex items-center gap-4 px-6 py-3">
                  <div className={cn(
                    'px-2.5 py-0.5 rounded-md text-[11px] font-semibold w-16 text-center flex-shrink-0',
                    t.riskLevel === 'Low' ? 'bg-success/10 text-success' :
                    t.riskLevel === 'Medium' ? 'bg-warning/10 text-warning' : 'bg-danger/10 text-danger'
                  )}>
                    {t.riskLevel}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-text-primary truncate">{t.title}</p>
                    <p className="text-xs text-text-muted">{t.district}, {t.state}</p>
                  </div>
                  <div className="hidden md:flex items-center gap-1 text-xs text-text-muted">
                    {t.missingDocuments.length === 0 ? (
                      <span className="text-success font-medium">All docs ready</span>
                    ) : (
                      <span className="text-warning">{t.missingDocuments.length} doc{t.missingDocuments.length > 1 ? 's' : ''} missing</span>
                    )}
                  </div>
                  <span className="text-xs font-semibold text-text-primary flex-shrink-0">{t.estimatedValue}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Jobs Tab */}
      {activeTab === 'Jobs' && (
        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Jobs by category */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Jobs by Category</h2>
              <div className="space-y-3">
                {jobsByCategory.map((c) => (
                  <div key={c.label}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-text-secondary">{c.label}</span>
                      <span className="text-xs font-semibold text-text-primary">{c.pct}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-surface-elevated overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${c.pct}%`, backgroundColor: c.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Total vacancies */}
            <div className="rounded-2xl border border-border-subtle bg-surface p-6">
              <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">Vacancy Summary</h2>
              <div className="space-y-3">
                {jobs.map((j) => (
                  <div key={j.id} className="flex items-center justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-text-secondary truncate">{j.title.substring(0, 38)}…</p>
                      <p className="text-[11px] text-text-muted">{j.state}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-sm font-bold text-text-primary font-heading">{j.vacancies.toLocaleString()}</span>
                      <span className="text-[10px] text-text-muted">posts</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-border-subtle flex items-center justify-between">
                <span className="text-xs text-text-muted">Total vacancies in DB</span>
                <span className="text-base font-bold font-heading text-text-primary">
                  {jobs.reduce((acc, j) => acc + j.vacancies, 0).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* AI match score distribution */}
          <div className="rounded-2xl border border-border-subtle bg-surface p-6">
            <h2 className="font-heading font-semibold text-sm text-text-primary mb-5">AI Match Score Distribution</h2>
            <div className="grid gap-3">
              {jobs.map((j) => (
                <div key={j.id} className="flex items-center gap-4">
                  <div className="w-40 flex-shrink-0">
                    <p className="text-xs text-text-secondary truncate">{j.title.substring(0, 28)}…</p>
                  </div>
                  <div className="flex-1 h-2 rounded-full bg-surface-elevated overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${j.matchScore}%`,
                        backgroundColor: j.matchScore >= 80 ? '#10B981' : j.matchScore >= 65 ? '#3B7CF4' : '#F59E0B',
                      }}
                    />
                  </div>
                  <span className={cn(
                    'text-xs font-bold w-8 text-right flex-shrink-0',
                    j.matchScore >= 80 ? 'text-success' : j.matchScore >= 65 ? 'text-brand-blue' : 'text-warning'
                  )}>
                    {j.matchScore}%
                  </span>
                  <span className="text-[11px] text-text-muted w-12 text-right flex-shrink-0">{j.deadline}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Sources Tab */}
      {activeTab === 'Sources' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border-subtle bg-surface overflow-hidden">
            <div className="px-6 py-4 border-b border-border-subtle flex items-center justify-between">
              <div>
                <h2 className="font-heading font-semibold text-sm text-text-primary">Data Sources &amp; Coverage</h2>
                <p className="text-xs text-text-muted mt-0.5">All portals, newspapers, and offline sources tracked by OPPORTA</p>
              </div>
              <span className="text-xs text-text-muted">{sourceBreakdown.length} active sources</span>
            </div>
            <div className="divide-y divide-border-subtle">
              {sourceBreakdown.map((s) => (
                <div key={s.source} className="flex items-center gap-4 px-6 py-4 hover:bg-surface-elevated transition-colors">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary">{s.source}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={cn(
                        'text-[11px] font-medium px-2 py-0.5 rounded',
                        s.type === 'Online' ? 'bg-brand-blue/10 text-brand-blue' :
                        s.type === 'Newspaper' ? 'bg-brand-cyan/10 text-brand-cyan' : 'bg-success/10 text-success'
                      )}>
                        {s.type}
                      </span>
                      <span className="text-[11px] text-text-muted">{s.state}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="hidden md:block w-24">
                      <div className="h-1.5 rounded-full bg-surface-elevated overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${s.pct}%`, backgroundColor: s.color }} />
                      </div>
                    </div>
                    <span className="text-sm font-bold font-heading text-text-primary w-12 text-right">{s.count.toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Coverage stats */}
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { label: 'Newspaper Sources', value: '312+', sub: 'Regional editions across CG & UP', icon: Newspaper, color: 'text-brand-cyan', bg: 'bg-brand-cyan/10' },
              { label: 'Online Portals', value: '14', sub: 'Official and verified source portals', icon: Activity, color: 'text-brand-blue', bg: 'bg-brand-blue/10' },
              { label: 'Last Full Sync', value: 'Today', sub: 'Auto-synced every 4 hours', icon: RefreshCw, color: 'text-success', bg: 'bg-success/10' },
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
