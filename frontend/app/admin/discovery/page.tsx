'use client'

import { useState } from 'react'
import {
  ShieldAlert, CheckCircle2, XCircle, AlertTriangle, RefreshCw,
  Clock, Globe, Newspaper, FileText, Eye, ChevronDown, ChevronUp,
  Database, Zap, Shield, Activity, Filter,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { adminQueue } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

type QueueStatus = 'Pending' | 'Approved' | 'Rejected' | 'CaptchaRequired'

const statusConfig: Record<QueueStatus, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  Pending:         { label: 'Pending Review', color: 'text-warning',    bg: 'bg-warning/10 border-warning/25',    icon: Clock },
  Approved:        { label: 'Approved',        color: 'text-success',    bg: 'bg-success/10 border-success/25',    icon: CheckCircle2 },
  Rejected:        { label: 'Rejected',         color: 'text-danger',    bg: 'bg-danger/10 border-danger/25',      icon: XCircle },
  CaptchaRequired: { label: 'CAPTCHA Block',   color: 'text-[#F97316]', bg: 'bg-[#F97316]/10 border-[#F97316]/25', icon: ShieldAlert },
}

const queueSummary = [
  { label: 'Total Batches',     value: adminQueue.length,                                          icon: Database,  color: 'text-brand-blue', bg: 'bg-brand-blue/10' },
  { label: 'Pending Review',    value: adminQueue.filter((q) => q.status === 'Pending').length,    icon: Clock,     color: 'text-warning',    bg: 'bg-warning/10' },
  { label: 'Approved Today',    value: adminQueue.filter((q) => q.status === 'Approved').length,   icon: CheckCircle2, color: 'text-success', bg: 'bg-success/10' },
  { label: 'CAPTCHA Blocks',    value: adminQueue.filter((q) => q.status === 'CaptchaRequired').length, icon: ShieldAlert, color: 'text-[#F97316]', bg: 'bg-[#F97316]/10' },
  {
    label: 'Total Opportunities',
    value: adminQueue.filter((q) => q.status === 'Approved').reduce((acc, q) => acc + q.opportunities, 0),
    icon: Zap,
    color: 'text-brand-cyan',
    bg: 'bg-brand-cyan/10',
  },
  { label: 'Rejected',          value: adminQueue.filter((q) => q.status === 'Rejected').length,  icon: XCircle,   color: 'text-danger',    bg: 'bg-danger/10' },
]

type LocalStatus = QueueStatus | 'unchanged'

export default function AdminPage() {
  const [filter, setFilter] = useState<QueueStatus | 'All'>('All')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [localStatuses, setLocalStatuses] = useState<Record<string, QueueStatus>>({})

  const getStatus = (id: string, original: QueueStatus): QueueStatus =>
    localStatuses[id] ?? original

  const setStatus = (id: string, status: QueueStatus) =>
    setLocalStatuses((prev) => ({ ...prev, [id]: status }))

  const filtered = adminQueue.filter((q) => {
    const status = getStatus(q.id, q.status)
    return filter === 'All' || status === filter
  })

  const pendingCount = adminQueue.filter((q) => getStatus(q.id, q.status) === 'Pending').length

  return (
    <AppShell isAdmin pageTitle="Admin Discovery Queue" pageSubtitle="Review and approve newly discovered opportunity batches">
      {/* Alert banner for pending items */}
      {pendingCount > 0 && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-warning/25 bg-warning/5 px-5 py-4">
          <AlertTriangle className="w-4 h-4 text-warning mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-text-primary">
              {pendingCount} batch{pendingCount > 1 ? 'es' : ''} awaiting review
            </p>
            <p className="text-xs text-text-muted mt-0.5">
              Review and approve or reject discovered batches before they are published to the platform.
            </p>
          </div>
        </div>
      )}

      {/* Summary KPI row */}
      <div className="grid grid-cols-3 lg:grid-cols-6 gap-3 mb-7">
        {queueSummary.map((s) => (
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
                ? f === 'All'
                  ? 'bg-brand-blue/15 text-brand-blue border-brand-blue/30'
                  : f === 'Pending'
                  ? 'bg-warning/15 text-warning border-warning/30'
                  : f === 'Approved'
                  ? 'bg-success/15 text-success border-success/30'
                  : f === 'CaptchaRequired'
                  ? 'bg-[#F97316]/15 text-[#F97316] border-[#F97316]/30'
                  : 'bg-danger/15 text-danger border-danger/30'
                : 'bg-surface text-text-secondary border-border-subtle hover:text-text-primary'
            )}
          >
            {f === 'CaptchaRequired' ? 'CAPTCHA Block' : f}
          </button>
        ))}
      </div>

      <p className="text-xs text-text-muted mb-4">Showing {filtered.length} of {adminQueue.length} batches</p>

      {/* Queue list */}
      <div className="space-y-3">
        {filtered.map((q) => {
          const status = getStatus(q.id, q.status)
          const cfg = statusConfig[status]
          const isExpanded = expanded === q.id
          const IconComponent = cfg.icon

          return (
            <div
              key={q.id}
              className={cn(
                'rounded-2xl border bg-surface overflow-hidden transition-all duration-200',
                status === 'Pending'
                  ? 'border-warning/20 hover:border-warning/35'
                  : status === 'CaptchaRequired'
                  ? 'border-[#F97316]/20 hover:border-[#F97316]/35'
                  : 'border-border-subtle hover:border-border-subtle'
              )}
            >
              {/* Main row */}
              <div className="flex items-start gap-4 p-5">
                {/* Source icon */}
                <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5',
                  q.type === 'Online' ? 'bg-brand-blue/10' : q.type === 'Newspaper' ? 'bg-brand-cyan/10' : 'bg-success/10'
                )}>
                  {q.type === 'Online' && <Globe className="w-4 h-4 text-brand-blue" />}
                  {q.type === 'Newspaper' && <Newspaper className="w-4 h-4 text-brand-cyan" />}
                  {q.type === 'Offline' && <FileText className="w-4 h-4 text-success" />}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <p className="text-sm font-semibold text-text-primary">{q.source}</p>
                    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border', cfg.bg, cfg.color)}>
                      <IconComponent className="w-3 h-3" />
                      {cfg.label}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-muted">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />Discovered: {q.discoveredAt}</span>
                    <span className="flex items-center gap-1"><Activity className="w-3 h-3" />{q.state}</span>
                    {q.opportunities > 0 && (
                      <span className="flex items-center gap-1 text-text-secondary font-medium">
                        <Zap className="w-3 h-3 text-brand-blue" />{q.opportunities} opportunities found
                      </span>
                    )}
                    {q.confidenceScore > 0 && (
                      <span className={cn(
                        'flex items-center gap-1 font-semibold',
                        q.confidenceScore >= 90 ? 'text-success' : q.confidenceScore >= 70 ? 'text-warning' : 'text-danger'
                      )}>
                        <Shield className="w-3 h-3" />AI confidence: {q.confidenceScore}%
                      </span>
                    )}
                  </div>

                  {/* Confidence bar */}
                  {q.confidenceScore > 0 && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="w-32 h-1 rounded-full bg-surface-elevated overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${q.confidenceScore}%`,
                            backgroundColor: q.confidenceScore >= 90 ? '#10B981' : q.confidenceScore >= 70 ? '#F59E0B' : '#EF4444',
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Notes preview */}
                  <p className="mt-2 text-xs text-text-muted italic">{q.notes}</p>
                </div>

                {/* Right: Actions */}
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  {/* Approve / Reject buttons — only show for Pending or CaptchaRequired */}
                  {(status === 'Pending' || status === 'CaptchaRequired') && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => setStatus(q.id, 'Approved')}
                        className="bg-success hover:bg-success/90 text-white font-semibold text-xs h-8 gap-1.5"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setStatus(q.id, 'Rejected')}
                        className="border-danger/30 text-danger hover:bg-danger/10 text-xs h-8 gap-1.5"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Reject
                      </Button>
                    </div>
                  )}

                  {/* Undo for approved / rejected */}
                  {(status === 'Approved' || status === 'Rejected') && localStatuses[q.id] && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setLocalStatuses((prev) => { const n = { ...prev }; delete n[q.id]; return n })}
                      className="border-border-subtle text-text-muted hover:text-text-primary text-xs h-8 gap-1.5"
                    >
                      <RefreshCw className="w-3 h-3" /> Undo
                    </Button>
                  )}

                  {/* Re-scrape for CAPTCHA */}
                  {status === 'CaptchaRequired' && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-[#F97316]/25 text-[#F97316] hover:bg-[#F97316]/10 text-xs h-8 gap-1.5"
                    >
                      <RefreshCw className="w-3 h-3" /> Retry Scrape
                    </Button>
                  )}

                  {/* Expand toggle */}
                  <button
                    onClick={() => setExpanded(isExpanded ? null : q.id)}
                    className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary transition-colors mt-1"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                </div>
              </div>

              {/* Expanded detail panel */}
              {isExpanded && (
                <div className="border-t border-border-subtle bg-surface-elevated px-5 py-4">
                  <div className="grid sm:grid-cols-3 gap-4 text-xs">
                    <div>
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">Batch ID</p>
                      <p className="text-text-secondary font-mono">{q.id}</p>
                    </div>
                    <div>
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">Source Type</p>
                      <p className="text-text-secondary">{q.type} — {q.state}</p>
                    </div>
                    <div>
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">CAPTCHA Required</p>
                      <p className={q.captchaRequired ? 'text-[#F97316]' : 'text-success'}>
                        {q.captchaRequired ? 'Yes — manual intervention needed' : 'No'}
                      </p>
                    </div>
                    <div className="sm:col-span-3">
                      <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">Admin Notes</p>
                      <p className="text-text-secondary">{q.notes}</p>
                    </div>
                    {status === 'Approved' && q.opportunities > 0 && (
                      <div className="sm:col-span-3">
                        <p className="text-text-muted font-medium mb-1 uppercase tracking-wide text-[10px]">Ingestion Status</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 rounded-full bg-background overflow-hidden max-w-xs">
                            <div className="h-full bg-success rounded-full w-full" />
                          </div>
                          <span className="text-success font-medium">{q.opportunities} listings ingested successfully</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}

        {filtered.length === 0 && (
          <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
            <Database className="w-8 h-8 text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary font-medium">No batches match this filter</p>
            <p className="text-sm text-text-muted mt-1">Try a different status filter above</p>
          </div>
        )}
      </div>

      {/* System status footer */}
      <div className="mt-8 rounded-xl border border-border-subtle bg-surface px-5 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-xs text-text-secondary font-medium">Discovery system running</span>
        </div>
        <div className="flex flex-wrap items-center gap-6 text-xs text-text-muted">
          <span className="flex items-center gap-1.5"><RefreshCw className="w-3 h-3" />Next sync in 3h 42m</span>
          <span className="flex items-center gap-1.5"><Globe className="w-3 h-3" />14 sources monitored</span>
          <span className="flex items-center gap-1.5"><Newspaper className="w-3 h-3" />312 newspaper sources</span>
          <span className="flex items-center gap-1.5"><Activity className="w-3 h-3" />Last run: Today 08:55</span>
        </div>
      </div>
    </AppShell>
  )
}
