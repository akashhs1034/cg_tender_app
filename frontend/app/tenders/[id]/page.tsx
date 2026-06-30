'use client'

import { useState, use } from 'react'
import Link from 'next/link'
import {
  ChevronLeft, MapPin, Clock, ExternalLink, FileEdit, Upload,
  Sparkles, CheckCircle2, AlertTriangle, XCircle, ArrowUpRight,
  FileText, Calendar, Shield, ClipboardList, History, RefreshCw,
  IndianRupee, Building2, Tag, Eye, TrendingUp,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { tenders } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { notFound } from 'next/navigation'

const tabs = [
  { id: 'overview', label: 'Overview', icon: Eye },
  { id: 'eligibility', label: 'Eligibility', icon: Shield },
  { id: 'dates', label: 'Important Dates', icon: Calendar },
  { id: 'documents', label: 'Documents Required', icon: FileText },
  { id: 'checklist', label: 'Bid Checklist', icon: ClipboardList },
  { id: 'intelligence', label: 'Tender Intelligence', icon: Sparkles },
  { id: 'source-history', label: 'Source History', icon: History },
  { id: 'corrigendum', label: 'Corrigendum History', icon: RefreshCw },
]

const riskColors: Record<string, string> = {
  Low: 'text-success bg-success/10 border-success/25',
  Medium: 'text-warning bg-warning/10 border-warning/25',
  High: 'text-danger bg-danger/10 border-danger/25',
}

export default function TenderDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const tender = tenders.find((t) => t.id === id)
  if (!tender) notFound()

  const [activeTab, setActiveTab] = useState('overview')

  return (
    <AppShell>
      {/* Back + Title */}
      <div className="mb-6">
        <Link href="/tenders" className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text-secondary transition-colors mb-4">
          <ChevronLeft className="w-4 h-4" /> Back to Tenders
        </Link>
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <BadgeMode mode={tender.mode} />
              <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded border border-border-subtle">{tender.category}</span>
              <AiMatchBadge score={tender.aiMatchScore} />
            </div>
            <h1 className="font-heading font-bold text-xl lg:text-2xl text-text-primary leading-snug text-balance">{tender.title}</h1>
            <p className="text-sm text-text-muted mt-1">{tender.nitNumber}</p>
          </div>
          <div className="flex flex-wrap gap-2 flex-shrink-0">
            <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold gap-1.5">
              <FileEdit className="w-3.5 h-3.5" /> Prepare Bid
            </Button>
            <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:bg-surface-elevated gap-1.5">
              <ExternalLink className="w-3.5 h-3.5" /> Open Source
            </Button>
          </div>
        </div>

        {/* Key info strip */}
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <span className="flex items-center gap-1.5 text-text-secondary"><Building2 className="w-3.5 h-3.5 text-text-muted" />{tender.department}</span>
          <span className="flex items-center gap-1.5 text-text-secondary"><MapPin className="w-3.5 h-3.5 text-text-muted" />{tender.district}, {tender.state}</span>
          <span className="flex items-center gap-1.5 text-text-primary font-semibold"><IndianRupee className="w-3.5 h-3.5 text-brand-blue" />{tender.estimatedValue.replace('₹', '')} Est. Value</span>
          <span className="flex items-center gap-1.5 text-danger font-medium"><Clock className="w-3.5 h-3.5" />Deadline: {tender.deadline}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-2 mb-6 border-b border-border-subtle">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-xs font-semibold whitespace-nowrap transition-colors',
              activeTab === tab.id
                ? 'text-brand-blue border-b-2 border-brand-blue -mb-px bg-brand-blue/5'
                : 'text-text-muted hover:text-text-secondary hover:bg-surface-elevated'
            )}
          >
            <tab.icon className="w-3.5 h-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {/* Overview */}
        {activeTab === 'overview' && (
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <h3 className="font-heading font-semibold text-sm text-text-primary mb-3">About this Tender</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{tender.description}</p>
              </div>
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <h3 className="font-heading font-semibold text-sm text-text-primary mb-3">Quick Details</h3>
                <dl className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'NIT Number', value: tender.nitNumber },
                    { label: 'State', value: tender.state },
                    { label: 'District', value: tender.district },
                    { label: 'Category', value: tender.category },
                    { label: 'Mode', value: tender.mode },
                    { label: 'Source', value: tender.source },
                    { label: 'Estimated Value', value: tender.estimatedValue },
                    { label: 'EMD', value: tender.emd },
                  ].map((item) => (
                    <div key={item.label}>
                      <dt className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-0.5">{item.label}</dt>
                      <dd className="text-xs text-text-secondary">{item.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
            <div className="space-y-4">
              <div className="rounded-xl border border-brand-blue/20 bg-brand-blue/5 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-brand-blue" />
                  <p className="text-sm font-semibold text-brand-blue">AI Match Score</p>
                </div>
                <div className="flex items-end gap-2 mb-2">
                  <p className="text-4xl font-heading font-bold text-text-primary">{tender.aiMatchScore}%</p>
                  <p className="text-xs text-success mb-1">Strong match</p>
                </div>
                <div className="h-2 rounded-full bg-surface-elevated overflow-hidden">
                  <div className="h-full bg-brand-blue rounded-full transition-all" style={{ width: `${tender.aiMatchScore}%` }} />
                </div>
                <button onClick={() => setActiveTab('intelligence')} className="mt-3 text-xs font-semibold text-brand-blue hover:underline">View full analysis →</button>
              </div>
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Bid Readiness</p>
                <div className="flex items-end gap-2 mb-2">
                  <p className="text-3xl font-heading font-bold text-text-primary">{tender.bidReadiness}%</p>
                </div>
                <div className="h-1.5 rounded-full bg-surface-elevated overflow-hidden">
                  <div className={cn('h-full rounded-full', tender.bidReadiness >= 80 ? 'bg-success' : tender.bidReadiness >= 60 ? 'bg-warning' : 'bg-danger')}
                    style={{ width: `${tender.bidReadiness}%` }} />
                </div>
                {tender.missingDocuments.length > 0 && (
                  <p className="text-xs text-warning mt-2">{tender.missingDocuments.length} document(s) missing</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Eligibility */}
        {activeTab === 'eligibility' && (
          <div className="max-w-2xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Eligibility Criteria</h3>
              <ul className="space-y-3">
                {tender.eligibility.map((e, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-text-secondary">
                    <CheckCircle2 className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Important Dates */}
        {activeTab === 'dates' && (
          <div className="max-w-lg">
            <div className="rounded-xl border border-border-subtle bg-surface p-6 space-y-4">
              {[
                { label: 'Tender Published', date: 'June 20, 2025' },
                { label: 'Pre-Bid Meeting', date: 'July 3, 2025' },
                { label: 'Last Date for Queries', date: 'July 5, 2025' },
                { label: 'Bid Submission Deadline', date: tender.deadline, highlight: true },
                { label: 'Bid Opening Date', date: 'July 20, 2025' },
              ].map((item) => (
                <div key={item.label} className={cn('flex items-center justify-between py-3 border-b border-border-subtle last:border-0', item.highlight && 'text-danger')}>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-text-muted" />
                    <span className="text-sm text-text-secondary">{item.label}</span>
                  </div>
                  <span className={cn('text-sm font-semibold', item.highlight ? 'text-danger' : 'text-text-primary')}>{item.date}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Documents Required */}
        {activeTab === 'documents' && (
          <div className="max-w-2xl space-y-4">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Required Documents</h3>
              <ul className="space-y-2.5">
                {tender.documents.map((doc, i) => {
                  const isMissing = tender.missingDocuments.includes(doc)
                  return (
                    <li key={i} className={cn('flex items-center justify-between px-3 py-2.5 rounded-lg border', isMissing ? 'border-warning/30 bg-warning/5' : 'border-border-subtle bg-surface-elevated')}>
                      <div className="flex items-center gap-2.5">
                        {isMissing ? <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0" /> : <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />}
                        <span className="text-sm text-text-secondary">{doc}</span>
                      </div>
                      {isMissing ? (
                        <span className="text-xs font-semibold text-warning">Missing</span>
                      ) : (
                        <span className="text-xs font-semibold text-success">Ready</span>
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center gap-2 mb-3">
                <Upload className="w-4 h-4 text-brand-blue" />
                <h4 className="font-semibold text-sm text-text-primary">Upload Company Documents</h4>
              </div>
              <p className="text-xs text-text-muted mb-3">Upload your documents once and reuse them across all tenders.</p>
              <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold gap-1.5 text-xs">
                <Upload className="w-3.5 h-3.5" /> Upload Documents
              </Button>
            </div>
          </div>
        )}

        {/* Bid Checklist */}
        {activeTab === 'checklist' && (
          <div className="max-w-2xl space-y-4">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-heading font-semibold text-base text-text-primary">Bid Preparation Checklist</h3>
                <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs gap-1.5">
                  <FileText className="w-3.5 h-3.5" /> Generate Draft Bid
                </Button>
              </div>
              <ul className="space-y-2">
                {[
                  { task: 'Review tender document and scope', done: true },
                  { task: 'Verify eligibility against criteria', done: true },
                  { task: 'Collect all required documents', done: tender.missingDocuments.length === 0 },
                  { task: 'Prepare company profile summary', done: true },
                  { task: 'Calculate estimated project cost', done: false },
                  { task: 'Arrange EMD / Bank Guarantee', done: false },
                  { task: 'Submit bid on portal before deadline', done: false },
                ].map((item, i) => (
                  <li key={i} className={cn('flex items-center gap-3 px-3 py-2.5 rounded-lg border text-sm', item.done ? 'border-success/20 bg-success/5 text-text-secondary' : 'border-border-subtle bg-surface-elevated text-text-secondary')}>
                    {item.done ? <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" /> : <div className="w-4 h-4 rounded-full border-2 border-border-subtle flex-shrink-0" />}
                    <span className={item.done ? 'line-through text-text-muted' : ''}>{item.task}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Tender Intelligence */}
        {activeTab === 'intelligence' && (
          <div className="space-y-5">
            {/* Header card */}
            <div className="rounded-xl border border-[#6C3EF4]/25 bg-[#6C3EF4]/5 p-5">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="w-4 h-4 text-[#6C3EF4]" />
                <h3 className="font-heading font-semibold text-sm text-text-primary">AI Tender Intelligence</h3>
              </div>
              <p className="text-xs text-text-muted">AI-powered analysis of this tender against your company profile.</p>
            </div>

            <div className="grid md:grid-cols-2 gap-5">
              {/* Match score */}
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Match Score</p>
                <div className="flex items-center gap-4">
                  <div className="relative w-20 h-20">
                    <svg className="w-20 h-20 -rotate-90" viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3.5" />
                      <circle cx="18" cy="18" r="15.9" fill="none" stroke="#3B7CF4" strokeWidth="3.5"
                        strokeDasharray={`${tender.aiMatchScore} ${100 - tender.aiMatchScore}`} strokeLinecap="round" />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center font-heading font-bold text-lg text-text-primary">{tender.aiMatchScore}%</span>
                  </div>
                  <div>
                    <p className="text-base font-semibold text-success">Strong Match</p>
                    <p className="text-xs text-text-muted mt-0.5">Your profile aligns well with this tender&apos;s requirements.</p>
                  </div>
                </div>
              </div>

              {/* Risk Level */}
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Risk Level</p>
                <div className={cn('inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-semibold', riskColors[tender.riskLevel])}>
                  <Shield className="w-4 h-4" /> {tender.riskLevel} Risk
                </div>
                <p className="text-xs text-text-muted mt-2">
                  {tender.riskLevel === 'Low' && 'This tender has straightforward requirements and a clear scope.'}
                  {tender.riskLevel === 'Medium' && 'Some requirements may need additional documentation or clarification.'}
                  {tender.riskLevel === 'High' && 'This tender has complex requirements. Review carefully before bidding.'}
                </p>
              </div>

              {/* Eligibility summary */}
              <div className="rounded-xl border border-border-subtle bg-surface p-5">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Eligibility Summary</p>
                <div className="space-y-2">
                  {[
                    { label: 'Contractor Registration', met: true },
                    { label: 'Annual Turnover', met: true },
                    { label: 'Prior Experience', met: true },
                    { label: 'GST Registration', met: true },
                    { label: 'Bank Solvency Certificate', met: tender.missingDocuments.length === 0 },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between text-xs">
                      <span className="text-text-secondary">{item.label}</span>
                      {item.met ? <CheckCircle2 className="w-3.5 h-3.5 text-success" /> : <XCircle className="w-3.5 h-3.5 text-danger" />}
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommended Action */}
              <div className="rounded-xl border border-brand-blue/20 bg-brand-blue/5 p-5">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Recommended Action</p>
                <div className="flex items-start gap-2.5">
                  <ArrowUpRight className="w-4 h-4 text-brand-blue mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-text-primary">Bid with confidence</p>
                    <p className="text-xs text-text-muted mt-1">
                      {tender.missingDocuments.length > 0
                        ? `Resolve ${tender.missingDocuments.length} missing document(s) before submitting. Your core eligibility is strong.`
                        : 'All eligibility criteria are met. Proceed to prepare and submit your bid.'}
                    </p>
                  </div>
                </div>
                {tender.missingDocuments.length > 0 && (
                  <div className="mt-3 space-y-1.5">
                    <p className="text-[10px] font-semibold text-warning uppercase tracking-wide">Missing Documents</p>
                    {tender.missingDocuments.map((doc) => (
                      <div key={doc} className="flex items-center gap-2 text-xs text-warning">
                        <AlertTriangle className="w-3 h-3 flex-shrink-0" /> {doc}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Bid Readiness */}
            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wide">Bid Readiness Checklist</p>
                <span className={cn('text-xs font-bold', tender.bidReadiness >= 80 ? 'text-success' : 'text-warning')}>{tender.bidReadiness}% Ready</span>
              </div>
              <div className="h-2 rounded-full bg-surface-elevated overflow-hidden mb-4">
                <div className={cn('h-full rounded-full', tender.bidReadiness >= 80 ? 'bg-success' : 'bg-warning')}
                  style={{ width: `${tender.bidReadiness}%` }} />
              </div>
              <div className="flex gap-3">
                <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs gap-1.5">
                  <FileText className="w-3.5 h-3.5" /> Generate Bid Checklist
                </Button>
                <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:bg-surface-elevated text-xs gap-1.5">
                  <FileEdit className="w-3.5 h-3.5" /> Generate Draft Bid File
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Source History */}
        {activeTab === 'source-history' && (
          <div className="max-w-2xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6">
              <h3 className="font-heading font-semibold text-base text-text-primary mb-4">Source History</h3>
              <div className="space-y-3">
                {[
                  { date: 'June 20, 2025 09:00 AM', event: 'Tender published on official portal', source: tender.source },
                  { date: 'June 20, 2025 09:45 AM', event: 'Detected and ingested by OPPORTA', source: 'Automated scan' },
                  { date: 'June 21, 2025 11:00 AM', event: 'AI analysis completed', source: 'AI Engine' },
                ].map((h, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <div className="flex flex-col items-center">
                      <div className="w-2 h-2 rounded-full bg-brand-blue mt-1.5" />
                      {i < 2 && <div className="w-px flex-1 bg-border-subtle mt-1" />}
                    </div>
                    <div className="pb-3">
                      <p className="text-text-primary font-medium">{h.event}</p>
                      <p className="text-xs text-text-muted mt-0.5">{h.date} · {h.source}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Corrigendum History */}
        {activeTab === 'corrigendum' && (
          <div className="max-w-2xl">
            <div className="rounded-xl border border-border-subtle bg-surface p-6 text-center py-12">
              <RefreshCw className="w-8 h-8 text-text-muted mx-auto mb-3" />
              <p className="text-text-secondary font-medium">No corrigendums issued</p>
              <p className="text-sm text-text-muted mt-1">We will notify you if this tender is amended.</p>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
