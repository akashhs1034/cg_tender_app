'use client'

import { Fragment, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  CheckCircle2, XCircle, AlertTriangle, CircleSlash, Clock, Database,
  Trash2, Archive, RefreshCw, Activity, Briefcase, FileText, CalendarX,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import type { SourceHealth, AdminOverview } from '@/lib/data'

const statusConfig: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  healthy:    { label: 'Working',    color: 'text-success', bg: 'bg-success/10 border-success/25', icon: CheckCircle2 },
  failed:     { label: 'Failed',     color: 'text-danger',  bg: 'bg-danger/10 border-danger/25',   icon: XCircle },
  no_records: { label: 'No records', color: 'text-warning', bg: 'bg-warning/10 border-warning/25', icon: AlertTriangle },
  not_run:    { label: 'Not run',    color: 'text-text-muted', bg: 'bg-surface-elevated border-border-subtle', icon: Clock },
  inactive:   { label: 'Inactive',   color: 'text-text-muted', bg: 'bg-surface-elevated border-border-subtle', icon: CircleSlash },
}

function fmtTime(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

type FilterKey = 'All' | 'healthy' | 'failed' | 'no_records'

export function AdminHealthClient({
  sources, overview,
}: { sources: SourceHealth[]; overview: AdminOverview }) {
  const router = useRouter()
  const { toast } = useToast()
  const [filter, setFilter] = useState<FilterKey>('All')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [busy, setBusy] = useState<'archive' | 'purge' | null>(null)

  const summary = useMemo(() => {
    const s = { healthy: 0, failed: 0, no_records: 0, other: 0, records: 0 }
    for (const src of sources) {
      s.records += src.recordCount
      if (src.status === 'healthy') s.healthy++
      else if (src.status === 'failed') s.failed++
      else if (src.status === 'no_records') s.no_records++
      else s.other++
    }
    return s
  }, [sources])

  const filtered = sources.filter((s) => filter === 'All' || s.status === filter)

  async function cleanup(mode: 'archive' | 'purge') {
    if (mode === 'purge' &&
        !window.confirm('Permanently DELETE all tenders & jobs past their deadline? This cannot be undone.')) {
      return
    }
    setBusy(mode)
    try {
      const res = await fetch('/api/admin/cleanup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
      const n = mode === 'purge'
        ? `${data.tendersDeleted ?? 0} tenders + ${data.jobsDeleted ?? 0} jobs deleted`
        : `${data.tendersArchived ?? 0} tenders + ${data.jobsArchived ?? 0} jobs archived`
      toast({ title: mode === 'purge' ? 'Expired data deleted' : 'Expired data archived', description: n })
      router.refresh()
    } catch (e) {
      toast({
        title: 'Cleanup failed',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      })
    } finally {
      setBusy(null)
    }
  }

  const tiles = [
    { label: 'Active tenders', value: overview.activeTenders, icon: FileText },
    { label: 'Active jobs', value: overview.totalJobs, icon: Briefcase },
    { label: 'New today', value: overview.newToday, icon: Activity },
    { label: 'Past deadline', value: overview.pastDeadline, icon: CalendarX },
  ]

  return (
    <AppShell isAdmin pageTitle="Source Health" pageSubtitle="What's working, what's failing, and when data last arrived">
      {/* Overview tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {tiles.map((t) => (
          <div key={t.label} className="rounded-xl border border-border-subtle bg-surface p-4">
            <div className="flex items-center gap-2 text-text-muted text-xs mb-1">
              <t.icon className="w-3.5 h-3.5" /> {t.label}
            </div>
            <p className="text-2xl font-semibold">{t.value.toLocaleString('en-IN')}</p>
          </div>
        ))}
      </div>

      {/* Cleanup card */}
      <div className="rounded-xl border border-border-subtle bg-surface p-4 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-medium flex items-center gap-2">
              <Database className="w-4 h-4 text-accent" /> Expired data cleanup
            </p>
            <p className="text-sm text-text-muted mt-0.5">
              {overview.pastDeadline.toLocaleString('en-IN')} tenders and {overview.pastDeadlineJobs.toLocaleString('en-IN')} jobs are past their deadline.
              Archive hides them from the app (reversible); Delete removes them permanently.
            </p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={busy !== null} onClick={() => cleanup('archive')}>
              {busy === 'archive'
                ? <RefreshCw className="w-4 h-4 mr-1.5 animate-spin" />
                : <Archive className="w-4 h-4 mr-1.5" />}
              Archive expired
            </Button>
            <Button size="sm" variant="destructive" disabled={busy !== null} onClick={() => cleanup('purge')}>
              {busy === 'purge'
                ? <RefreshCw className="w-4 h-4 mr-1.5 animate-spin" />
                : <Trash2 className="w-4 h-4 mr-1.5" />}
              Delete permanently
            </Button>
          </div>
        </div>
      </div>

      {/* Source status summary + filter */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {([
          ['All', `All (${sources.length})`],
          ['healthy', `Working (${summary.healthy})`],
          ['no_records', `No records (${summary.no_records})`],
          ['failed', `Failed (${summary.failed})`],
        ] as [FilterKey, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm border transition-colors',
              filter === key
                ? 'bg-accent/15 border-accent/40 text-accent'
                : 'bg-surface border-border-subtle text-text-muted hover:text-text-primary',
            )}
          >
            {label}
          </button>
        ))}
        <span className="ml-auto text-xs text-text-muted">
          Last ingestion: {fmtTime(overview.lastIngestAt)}
        </span>
      </div>

      {/* Sources table */}
      {sources.length === 0 ? (
        <div className="rounded-xl border border-border-subtle bg-surface p-8 text-center text-text-muted">
          No source health data yet — it appears after the next scraper run.
        </div>
      ) : (
        <div className="rounded-xl border border-border-subtle bg-surface overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-subtle text-left text-xs text-text-muted uppercase tracking-wider">
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Kind</th>
                  <th className="px-4 py-3">State</th>
                  <th className="px-4 py-3 text-right">Records</th>
                  <th className="px-4 py-3">Last run</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => {
                  const cfg = statusConfig[s.status] ?? statusConfig.not_run
                  const Icon = cfg.icon
                  const isOpen = expanded === s.sourceId
                  return (
                    <Fragment key={s.sourceId}>
                      <tr
                        className={cn(
                          'border-b border-border-subtle/60 hover:bg-surface-elevated/50',
                          s.error && 'cursor-pointer',
                        )}
                        onClick={() => s.error && setExpanded(isOpen ? null : s.sourceId)}
                      >
                        <td className="px-4 py-2.5">
                          <span className={cn('inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border text-xs', cfg.bg, cfg.color)}>
                            <Icon className="w-3.5 h-3.5" /> {cfg.label}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 font-medium">{s.displayName}</td>
                        <td className="px-4 py-2.5 text-text-muted">{s.kind}</td>
                        <td className="px-4 py-2.5 text-text-muted">{s.state ?? '—'}</td>
                        <td className="px-4 py-2.5 text-right tabular-nums">{s.recordCount.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-2.5 text-text-muted whitespace-nowrap">{fmtTime(s.runAt)}</td>
                      </tr>
                      {isOpen && s.error && (
                        <tr className="border-b border-border-subtle/60 bg-danger/5">
                          <td colSpan={6} className="px-4 py-2.5 text-xs text-danger font-mono break-all">
                            {s.error}
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppShell>
  )
}
