'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Sparkles, Shield, CheckCircle2, AlertTriangle, ArrowUpRight, Loader2 } from 'lucide-react'
import { Modal } from '@/components/ui/modal'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { Tender } from '@/lib/mock-data'

const riskColors: Record<string, string> = {
  Low: 'text-success bg-success/10 border-success/25',
  Medium: 'text-warning bg-warning/10 border-warning/25',
  High: 'text-danger bg-danger/10 border-danger/25',
}

/** Mock AI analysis panel for a tender — derived entirely from local mock data. */
export function TenderAnalysisDialog({ tender, open, onClose }: { tender: Tender | null; open: boolean; onClose: () => void }) {
  const [ai, setAi] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const runAnalysis = async () => {
    if (!tender) return
    setLoading(true)
    try {
      const res = await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: tender.title, department: tender.department, category: tender.category,
          state: tender.state, estimatedValue: tender.estimatedValue, emd: tender.emd,
          deadline: tender.deadline, eligibility: tender.eligibility, description: tender.description,
        }),
      })
      const data = await res.json()
      setAi(
        data?.ok && data.text
          ? data.text
          : data?.reason === 'no_key'
            ? 'AI analysis needs GEMINI_API_KEY to be configured on the server.'
            : 'AI analysis is unavailable right now.'
      )
    } catch {
      setAi('AI analysis is unavailable right now.')
    } finally {
      setLoading(false)
    }
  }

  if (!tender) return null
  const matchLabel = tender.aiMatchScore >= 85 ? 'Strong match' : tender.aiMatchScore >= 70 ? 'Good match' : 'Fair match'

  return (
    <Modal
      open={open}
      onClose={onClose}
      eyebrow="AI Analysis"
      title={tender.title}
      accent="blue"
      icon={<Sparkles className="h-4 w-4" />}
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} className="text-xs h-8">Close</Button>
          <Link href={`/tenders/${tender.id}`}>
            <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white text-xs h-8 gap-1.5">
              <ArrowUpRight className="h-3.5 w-3.5" /> Full analysis
            </Button>
          </Link>
        </>
      }
    >
      <div className="space-y-4">
        {/* Match score */}
        <div className="rounded-xl border border-brand-blue/20 bg-brand-blue/5 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">AI Match Score</p>
          <div className="mt-1 flex items-end gap-2">
            <p className="font-heading text-3xl font-bold text-text-primary">{tender.aiMatchScore}%</p>
            <p className="mb-1 text-xs font-medium text-success">{matchLabel}</p>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-elevated">
            <div className="h-full rounded-full bg-brand-blue" style={{ width: `${tender.aiMatchScore}%` }} />
          </div>
        </div>

        {/* Risk + readiness */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-border-subtle bg-surface-elevated p-3">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-text-muted">Risk Level</p>
            <span className={cn('inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold', riskColors[tender.riskLevel])}>
              <Shield className="h-3.5 w-3.5" /> {tender.riskLevel}
            </span>
          </div>
          <div className="rounded-xl border border-border-subtle bg-surface-elevated p-3">
            <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-text-muted">Bid Readiness</p>
            <p className={cn('font-heading text-xl font-bold', tender.bidReadiness >= 80 ? 'text-success' : tender.bidReadiness >= 60 ? 'text-warning' : 'text-danger')}>
              {tender.bidReadiness}%
            </p>
          </div>
        </div>

        {/* Eligibility */}
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-text-muted">Key Eligibility</p>
          <ul className="space-y-1.5">
            {tender.eligibility.slice(0, 4).map((e, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-success" /> {e}
              </li>
            ))}
          </ul>
        </div>

        {/* Recommended action */}
        <div className="rounded-xl border border-border-subtle bg-surface-elevated p-4">
          <p className="text-sm font-semibold text-text-primary">Recommended action</p>
          <p className="mt-1 text-xs text-text-muted">
            {tender.missingDocuments.length > 0
              ? `Resolve ${tender.missingDocuments.length} missing document(s) before submitting — your core eligibility is strong.`
              : 'All eligibility criteria are met. Proceed to prepare and submit your bid.'}
          </p>
          {tender.missingDocuments.length > 0 && (
            <div className="mt-2 space-y-1">
              {tender.missingDocuments.map((d) => (
                <p key={d} className="flex items-center gap-1.5 text-xs text-warning">
                  <AlertTriangle className="h-3 w-3 flex-shrink-0" /> {d}
                </p>
              ))}
            </div>
          )}
        </div>
        {/* AI analysis (Gemini) */}
        <div className="rounded-xl border border-brand-blue/20 bg-brand-blue/5 p-4">
          <div className="flex items-center justify-between gap-2">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-brand-blue">
              <Sparkles className="h-4 w-4" /> AI Analysis
            </p>
            <Button size="sm" onClick={runAnalysis} disabled={loading}
              className="btn-glow bg-brand-blue hover:bg-brand-blue/90 text-white text-xs h-8 gap-1.5">
              {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
              {loading ? 'Analyzing…' : ai ? 'Regenerate' : 'Generate'}
            </Button>
          </div>
          {ai ? (
            <pre className="mt-3 whitespace-pre-wrap font-sans text-xs leading-relaxed text-text-secondary">{ai}</pre>
          ) : (
            <p className="mt-2 text-xs text-text-muted">Generate a live AI assessment of eligibility, risk, and recommended action for this tender.</p>
          )}
        </div>
      </div>
    </Modal>
  )
}
