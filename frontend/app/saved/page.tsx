'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Bookmark, BookmarkCheck, MapPin, Clock, Eye, FileText, Loader2, LogIn,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageHero } from '@/components/page-hero'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { useSaved } from '@/lib/saved-context'
import { useAuth } from '@/lib/auth-context'
import { getTendersByIds } from '@/lib/data'
import type { Tender } from '@/lib/mock-data'

export default function SavedPage() {
  const { savedIds, ready, toggleSaved } = useSaved()
  const { user } = useAuth()
  const { toast } = useToast()
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loading, setLoading] = useState(true)

  const idKey = [...savedIds].sort().join(',')

  useEffect(() => {
    if (!ready) return
    let active = true
    setLoading(true)
    getTendersByIds([...savedIds])
      .then((rows) => {
        if (active) setTenders(rows)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [idKey, ready]) // eslint-disable-line react-hooks/exhaustive-deps

  const remove = async (t: Tender) => {
    await toggleSaved(t)
    setTenders((prev) => prev.filter((x) => x.id !== t.id))
    toast('Removed from saved', 'info')
  }

  return (
    <AppShell pageTitle="Saved" pageSubtitle="Your saved tenders pipeline">
      <PageHero
        variant="dashboard"
        eyebrow="My Pipeline"
        icon={<Bookmark className="h-3.5 w-3.5" />}
        title="Saved Tenders"
        subtitle={
          user
            ? 'Tenders you have saved, synced to your account across devices.'
            : 'Tenders you have saved on this device. Sign in to sync them everywhere.'
        }
      >
        {!user && (
          <Link href="/login" className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-xs font-semibold text-white transition-colors hover:bg-brand-blue/90">
            <LogIn className="h-3.5 w-3.5" /> Sign in to sync
          </Link>
        )}
      </PageHero>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-text-muted">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading your saved tenders…
        </div>
      ) : tenders.length === 0 ? (
        <div className="text-center py-16 rounded-2xl border border-border-subtle bg-surface">
          <Bookmark className="w-8 h-8 text-text-muted mx-auto mb-3" />
          <p className="text-text-secondary font-medium">No saved tenders yet</p>
          <p className="text-sm text-text-muted mt-1">Tap the bookmark on any tender to add it to your pipeline.</p>
          <Link href="/tenders" className="inline-flex items-center gap-1.5 mt-4 rounded-lg bg-brand-blue px-4 py-2 text-xs font-semibold text-white hover:bg-brand-blue/90 transition-colors">
            <FileText className="h-3.5 w-3.5" /> Browse Tenders
          </Link>
        </div>
      ) : (
        <>
          <p className="text-xs text-text-muted mb-4">{tenders.length} saved tender{tenders.length > 1 ? 's' : ''}</p>
          <div className="grid gap-4">
            {tenders.map((t) => (
              <div key={t.id} className="rounded-2xl border border-border-subtle bg-surface hover:border-brand-blue/25 transition-all duration-200 p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <BadgeMode mode={t.mode} />
                      <span className="text-[11px] text-text-muted font-medium bg-surface-elevated px-2 py-0.5 rounded">{t.category}</span>
                    </div>
                    <h3 className="font-heading font-semibold text-base text-text-primary leading-snug line-clamp-2">{t.title}</h3>
                    <p className="text-xs text-text-muted mt-1">{t.nitNumber}</p>
                  </div>
                  <AiMatchBadge score={t.aiMatchScore} className="flex-shrink-0 mt-1" />
                </div>
                <div className="flex flex-wrap items-center gap-4 mb-4 text-xs text-text-secondary">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{t.district}, {t.state === 'Chhattisgarh' ? 'CG' : 'UP'}</span>
                  <span className="font-semibold text-text-primary">{t.estimatedValue}</span>
                  <span className="flex items-center gap-1.5"><Clock className="w-3 h-3 text-danger" /><span className="text-danger font-medium">Deadline: {t.deadline}</span></span>
                </div>
                <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
                  <Link href={`/tenders/${t.id}`}>
                    <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs h-8 gap-1.5">
                      <Eye className="w-3.5 h-3.5" /> View Details
                    </Button>
                  </Link>
                  {t.documentUrl && (
                    <a href={t.documentUrl} target="_blank" rel="noopener noreferrer">
                      <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated text-xs h-8 gap-1.5">
                        <FileText className="w-3.5 h-3.5" /> Document
                      </Button>
                    </a>
                  )}
                  <Button size="sm" variant="outline" onClick={() => remove(t)}
                    className="border-brand-blue/40 text-brand-blue bg-brand-blue/10 hover:bg-brand-blue/15 text-xs h-8 gap-1.5">
                    <BookmarkCheck className="w-3.5 h-3.5" /> Saved
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </AppShell>
  )
}
