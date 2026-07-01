'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react'

/**
 * App-wide error boundary. Chunk-load errors (common right after a new deploy,
 * when an open tab requests JS chunks the latest build replaced) are transient —
 * we reload the page once automatically to fetch the fresh assets. Other errors
 * show a friendly, recoverable screen instead of a blank "couldn't load".
 */
export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    const msg = `${error?.name ?? ''} ${error?.message ?? ''}`.toLowerCase()
    const isChunkError =
      msg.includes('chunk') || msg.includes('failed to fetch dynamically imported module') || msg.includes('loading css chunk')
    if (isChunkError && typeof window !== 'undefined') {
      const KEY = 'opporta:chunk-reloaded'
      if (!sessionStorage.getItem(KEY)) {
        sessionStorage.setItem(KEY, '1')
        window.location.reload()
      }
    }
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-surface p-8 text-center shadow-2xl shadow-black/40">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-danger/10">
          <AlertTriangle className="h-6 w-6 text-danger" />
        </div>
        <h1 className="font-heading text-xl font-bold text-text-primary">Something went wrong</h1>
        <p className="mt-2 text-sm text-text-secondary">
          This page hit an error while loading. This can happen right after an update — reloading usually fixes it.
        </p>
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => reset()}
            className="btn-glow inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-blue/90"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Try again
          </button>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle px-4 py-2 text-sm font-semibold text-text-secondary transition-colors hover:bg-surface-elevated hover:text-text-primary"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Go to dashboard
          </Link>
        </div>
        {error?.digest && <p className="mt-4 text-[10px] text-text-muted">Ref: {error.digest}</p>}
      </div>
    </div>
  )
}
