'use client'

import { useMemo, useState } from 'react'
import {
  ShieldAlert, CheckCircle2, XCircle, AlertTriangle, RefreshCw,
  Clock, Globe, Newspaper, FileText, Eye, ChevronDown, ChevronUp,
  Database, Zap, Shield, Activity, Filter, ExternalLink,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import type { DiscoveredSource } from '@/lib/data'

type UiStatus = 'Pending' | 'Approved' | 'Rejected' | 'CaptchaRequired'

const statusConfig: Record<UiStatus, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  Pending: { label: 'Pending Review', color: 'text-warning', bg: 'bg-warning/10 border-warning/25', icon: Clock },
  Approved: { label: 'Approved', color: 'text-success', bg: 'bg-success/10 border-success/25', icon: CheckCircle2 },
  Rejected: { label: 'Rejected', color: 'text-danger', bg: 'bg-danger/10 border-danger/25', icon: XCircle },
  CaptchaRequired: { label: 'CAPTCHA Block', color: 'text-[#F97316]', bg: 'bg-[#F97316]/10 border-[#F97316]/25', icon: ShieldAlert },
}

/** Map raw DB status → UI status bucket. */
function toUiStatus(s: DiscoveredSource): UiStatus {
  if (s.requiresCaptcha) return 'CaptchaRequired'
  const v = s.status.toLowerCase()
  if (v.includes('approv') || v === 'active') return 'Approved'
  if (v.includes('reject')) return 'Rejected'
  return 'Pending'
}

function iconFor(type: string) {
  if (type.includes('news') || type.includes('epaper')) return Newspaper
  if (type.includes('portal') || type.includes('site')) return Globe
  return FileText
}

export function AdminDiscoveryClient({ sources }: { sources: DiscoveredSource[] }) {
  const [filter, setFilter] = useState<UiStatus | 'All'>('All')
  const [expanded, setExpanded] = useState<number | null>(null)
  const [overrides, setOverrides] = useState<Record<number, UiStatus>>({})
  const { toast } = useToast()

  const getStatus = (s: DiscoveredSource): UiStatus => overrides[s.id] ?? toUiStatus(s)
  const setStatus = (id: number, status: UiStatus) => setOverrides((p) => ({ ...p, [id]: status }))

  const filtered = sources.filter((s) => filter === 'All' || getStatus(s) === filter)

  const summary = useMemo(() => {
    const counts = { total: sources.length, pending: 0, approved: 0, rejected: 0, captcha: 0 }
    for (const s of sources) {
      const st = getStatus(s)
      if (st === 'Pending') counts.pending++
      else if (st === 'Approved') counts.approved++
      else if (st === 'Rejected') counts.rejected++
      else counts.captcha++
    }
    return counts
  }, [sources, overrides]) // eslint-disable-line react-hooks/exhaustive-deps

  const kpis = [
    { label: 'Total Sources', value: summary.total, icon: Database, color: 'text-brand-blue', bg: 'bg-brand-blue/10' },
    { label: 'Pending Review', value: summary.pending, icon: Clock, color: 'text-warning', bg: 'bg-warning/10' },
    { label: 'Approved', value: summary.approved, icon: CheckCircle2, color: 'text-success', bg: 'bg-success/10' },
    { label: 'CAPTCHA Blocks', value: summary.captcha, icon: ShieldAlert, color: 'text-[#F97316]', bg: 'bg-[#F97316]/10' },
    { label: 'Avg Confidence', value: sources.length ? `${Math.round(sources.reduce((a, s) => a + s.confidenceScore, 0) / sources.length)}%` : '—', icon: Zap, color: 'text-brand-cyan', bg: 'bg-brand-cyan/10' },
    { label: 'Rejected', value: summary.rejected, icon: XCircle, color: 'text-danger', bg: 'bg-danger/10' },
  ]

  return (
    <AppShell isAdmin pageTitle="Admin Discovery Queue" pageSubtitle="Review newly discovered opportunity sources">
      {sources.length === 0 ? (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-warning/25 bg-warning/5 px-5 py-4">
          <AlertTriangle className="w-4 h-4 text-warning mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-text-primary">No discovered sources loaded</p>
            <p className="text-xs text-text-muted mt-0.5">The discovery queue is empty or could not be reached. Check back after the next discovery run.</p>
          </div>
        </div>
      ) : (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-brand-blue/25 bg-brand-blue/5 px-5 py-4">
          <Database className="w-4 h-4 text-brand-blue mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-text-primary">Live discovery data</p>
            <p className="text-xs text-text-muted mt-0.5">
              Sources are read live from the discovery pipeline. Approve / reject actions are local previews until the admin write API is connected.
            </p>
          </div>
        </div>
      )}

      {/* Summary KPI row */}
      <div className="grid grid-cols-3 lg:grid-cols-6 gap-3 mb-7">
        {kpis.map((s) => (
          <div key={s.label} className="rounded-xl border border-border-subtle bg-surface p-4">
            <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center mb-2.5', s.bg)}>
              <s.icon className={cn('w-3.5 h-3.5', s.color)} />
            </div>
            <p className={cn('font-heading font-bold text-xl', s.color)}>{s.value}</p>
            <p className="text-[11px] text-text-muted mt-0.5 leading-tight">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-2 mb-5 flex-wrap">
        <span className="text-xs text-text-muted flex items-center gap-1.5 mr-1"><Filter className="w-3.5 h-3.5" />Filter:</span>
        {(['All', 'Pending', 'Approved', 'Rejected', 'CaptchaRequired'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              'px-3 py-1 rounded-md text-xs font-medium border transition-colors',
              filter === f
                ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30'
                : 'bg-surface text-text-secondary border-border-subtle hover:text-text-primary'
            )}
          >
            {f === 'CaptchaRequired' ? 'CAPTCHA Block' : f}
          </button>
        ))}
      </div>

      <p className="text-xs text-text-muted mb-4">Showing {filtered.length} of {sources.length} sources</p>

      {/* Source list */}
      <div className="space-y-3">
        {filtered.map((s) => {
          const status = getStatus(s)
          const cfg = statusConfig[status]
          const isExpanded = expanded === s.id
          const SourceIcon = iconFor(s.sourceType)
          const StatusIcon = cfg.icon

          return (
            <div key={s.id} className="rounded-2xl border border-border-subtle bg-surface overflow-hidden transition-all duration-200 hover:border-brand-blue/25">
              <div className="flex items-start gap-4 p-5">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 bg-brand-blue/10">
                  <SourceIcon className="w-4 h-4 text-brand-blue" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <p className="text-sm font-semibold text-text-primary truncate max-w-md">{s.title}</p>
                    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border', cfg.bg, cfg.color)}>
                      <StatusIcon className="w-3 h-3" />
                      {cfg.label}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
                    <span className="flex items-center gap-1"><Globe className="w-3 h-3" />{s.domain || s.url}</span>
                    <span className="flex items-center gap-1"><Activity className="w-3 h-3" />{s.state} · {s.sourceType}</span>
                    {s.confidenceScore > 0 && (
                      <span className={cn('flex items-center gap-1 font-semibold',
                        s.confidenceScore >= 90 ? 'text-success' : s.confidenceScore >= 70 ? 'text-warning' : 'text-danger')}>
                        <Shield className="w-3 h-3" />Confidence: {s.confidenceScore}%
                      </span>
                    )}
                  </div>
                  {s.confidenceScore > 0 && (
                    <div className="mt-2 w-32 h-1 rounded-full bg-surface-elevated overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${s.confidenceScore}%`, backgroundColor: s.confidenceScore >= 90 ? '#10B981' : s.confidenceScore >= 70 ? '#F59E0B' : '#EF4444' }} />
                    </div>
                  )}
                  {s.reason && <p className="mt-2 text-xs text-text-muted italic">{s.reason}</p>}
                </div>

                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  {(status === 'Pending' || status === 'CaptchaRequired') && (
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => { setStatus(s.id, 'Approved'); toast('Source approved', 'success', { description: s.domain || s.title }) }}
                        className="bg-success hover:bg-success/90 text-white font-semibold text-xs h-8 gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => { setStatus(s.id, 'Rejected'); toast('Source rejected', 'info', { description: s.domain || s.title }) }}
                        className="border-danger/30 text-danger hover:bg-danger/10 text-xs h-8 gap-1.5">
                        <XCircle className="w-3.5 h-3.5" /> Reject
                      </Button>
                    </div>
                  )}
                  {(status === 'Approved' || status === 'Rejected') && overrides[s.id] && (
                    <Button size="sm" variant="outline" onClick={() => { setOverrides((p) => { const n = { ...p }; delete n[s.id]; return n }); toast('Reverted', 'info') }}
                      className="border-border-subtle text-text-muted hover:text-text-primary text-xs h-8 gap-1.5">
                      <RefreshCw className="w-3 h-3" /> Undo
                    </Button>
                  )}
                  <button onClick={() => setExpanded(isExpanded ? null : s.id)} className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary transition-colors mt-1">
                    <Eye className="w-3.5 h-3.5" />
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="border-t border-border-subtle bg-surface-elevated px-5 py-4">
                  <div className="grid sm:grid-cols-3 gap-4 text-xs">
                    <div>
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">Category</p>
                      <p className="text-text-secondary">{s.category}</p>
                    </div>
                    <div>
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">Raw status</p>
                      <p className="text-text-secondary font-mono">{s.status}</p>
                    </div>
                    <div>
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">CAPTCHA</p>
                      <p className={s.requiresCaptcha ? 'text-[#F97316]' : 'text-success'}>{s.requiresCaptcha ? 'Yes — manual intervention' : 'No'}</p>
                    </div>
                    <div className="sm:col-span-3">
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">URL</p>
                      <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-brand-blue hover:underline inline-flex items-center gap-1 break-all">
                        {s.url} <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}

        {sources.length > 0 && filtered.length === 0 && (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <Database className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">No sources match this filter</p>
            <p className="text-sm text-text-muted mt-1">Try a different status filter above</p>
          </div>
        )}
      </div>
    </AppShell>
  )
}
