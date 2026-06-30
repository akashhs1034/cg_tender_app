'use client'

import Link from 'next/link'
import { CheckCircle2, ShieldCheck, ArrowUpRight, GraduationCap } from 'lucide-react'
import { Modal } from '@/components/ui/modal'
import { Button } from '@/components/ui/button'
import type { Job } from '@/lib/mock-data'

/** Mock eligibility panel for a job — derived entirely from local mock data. */
export function JobEligibilityDialog({ job, open, onClose }: { job: Job | null; open: boolean; onClose: () => void }) {
  if (!job) return null
  const verdict = job.matchScore >= 70 ? 'You likely qualify' : 'Review criteria carefully'

  return (
    <Modal
      open={open}
      onClose={onClose}
      eyebrow="Eligibility Check"
      title={job.title}
      accent="purple"
      icon={<ShieldCheck className="h-4 w-4" />}
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} className="text-xs h-8">Close</Button>
          <Link href={`/jobs/${job.id}`}>
            <Button size="sm" className="bg-[#6C3EF4] hover:bg-[#6C3EF4]/90 text-white text-xs h-8 gap-1.5">
              <ArrowUpRight className="h-3.5 w-3.5" /> Full details
            </Button>
          </Link>
        </>
      }
    >
      <div className="space-y-4">
        {/* Verdict */}
        <div className="rounded-xl border border-[#6C3EF4]/20 bg-[#6C3EF4]/5 p-4">
          <div className="flex items-end gap-2">
            <p className="font-heading text-3xl font-bold text-text-primary">{job.matchScore}%</p>
            <p className="mb-1 text-xs font-semibold text-[#6C3EF4]">{verdict}</p>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-elevated">
            <div className="h-full rounded-full bg-[#6C3EF4]" style={{ width: `${job.matchScore}%` }} />
          </div>
        </div>

        {/* Key facts */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-border-subtle bg-surface-elevated p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-text-muted">Qualification</p>
            <p className="mt-0.5 text-xs text-text-secondary">{job.qualification}</p>
          </div>
          <div className="rounded-xl border border-border-subtle bg-surface-elevated p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-text-muted">Age Limit</p>
            <p className="mt-0.5 text-xs text-text-secondary">{job.ageLimit}</p>
          </div>
        </div>

        {/* Eligibility criteria */}
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-text-muted">Eligibility Criteria</p>
          <ul className="space-y-1.5">
            {job.eligibility.map((e, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-success" /> {e}
              </li>
            ))}
          </ul>
        </div>

        {/* Selection process */}
        <div className="rounded-xl border border-border-subtle bg-surface-elevated p-4">
          <div className="mb-2 flex items-center gap-1.5">
            <GraduationCap className="h-3.5 w-3.5 text-[#6C3EF4]" />
            <p className="text-xs font-semibold text-text-primary">Selection Process</p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {job.selectionProcess.map((s, i) => (
              <span key={i} className="rounded-md border border-border-subtle bg-surface px-2 py-0.5 text-[11px] text-text-secondary">
                {i + 1}. {s}
              </span>
            ))}
          </div>
        </div>
        <p className="text-[10px] text-text-muted">Demo eligibility check from sample data — personalised matching connects after backend integration.</p>
      </div>
    </Modal>
  )
}
