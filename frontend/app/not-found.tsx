import Link from 'next/link'
import { FileQuestion, ArrowLeft, FileText } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-surface p-8 text-center shadow-2xl shadow-black/40">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-blue/10">
          <FileQuestion className="h-6 w-6 text-brand-blue" />
        </div>
        <h1 className="font-heading text-xl font-bold text-text-primary">Not found</h1>
        <p className="mt-2 text-sm text-text-secondary">
          This tender or job may have expired or been removed. Try browsing the latest opportunities.
        </p>
        <div className="mt-6 flex items-center justify-center gap-2">
          <Link
            href="/tenders"
            className="btn-glow inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-blue/90"
          >
            <FileText className="h-3.5 w-3.5" /> Browse tenders
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle px-4 py-2 text-sm font-semibold text-text-secondary transition-colors hover:bg-surface-elevated hover:text-text-primary"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
