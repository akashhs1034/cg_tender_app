'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/lib/auth-context'
import type { Tender } from '@/lib/mock-data'

/** Minimal shape needed to persist a saved tender. */
export interface SavableTender {
  id: string
  title: string
  state?: string
  department?: string
  deadline?: string
  sector?: string
  sourceUrl?: string
}

interface SavedState {
  savedIds: Set<string>
  isSaved: (id: string) => boolean
  /** Toggles saved state; returns the new state (true = now saved). */
  toggleSaved: (t: Tender | SavableTender) => Promise<boolean>
  ready: boolean
}

const SavedContext = createContext<SavedState>({
  savedIds: new Set(),
  isSaved: () => false,
  toggleSaved: async () => false,
  ready: false,
})

const GUEST_KEY = 'opporta:saved-tenders'

function readGuest(): string[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(window.localStorage.getItem(GUEST_KEY) ?? '[]')
  } catch {
    return []
  }
}

function writeGuest(ids: string[]) {
  try {
    window.localStorage.setItem(GUEST_KEY, JSON.stringify(ids))
  } catch {
    /* storage unavailable — ignore */
  }
}

export function SavedProvider({ children }: { children: React.ReactNode }) {
  const supabase = useMemo(() => createClient(), [])
  const { user, email } = useAuth()
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  const [ready, setReady] = useState(false)

  // Load saved set whenever auth state changes.
  useEffect(() => {
    let active = true
    setReady(false)

    async function load() {
      if (user && email) {
        const { data, error } = await supabase
          .from('saved_tenders')
          .select('source_id')
          .eq('email', email)
        if (!active) return
        if (error) {
          // Fall back to whatever the guest had locally.
          setSavedIds(new Set(readGuest()))
        } else {
          setSavedIds(new Set((data ?? []).map((r) => r.source_id).filter(Boolean) as string[]))
        }
      } else {
        setSavedIds(new Set(readGuest()))
      }
      if (active) setReady(true)
    }

    load()
    return () => {
      active = false
    }
  }, [user, email, supabase])

  const toggleSaved = useCallback(
    async (t: Tender | SavableTender): Promise<boolean> => {
      const currentlySaved = savedIds.has(t.id)
      const next = new Set(savedIds)

      // Optimistic update.
      if (currentlySaved) next.delete(t.id)
      else next.add(t.id)
      setSavedIds(next)

      if (user && email) {
        if (currentlySaved) {
          const { error } = await supabase
            .from('saved_tenders')
            .delete()
            .eq('email', email)
            .eq('source_id', t.id)
          if (error) {
            setSavedIds(savedIds) // revert
            return currentlySaved
          }
        } else {
          const dept = 'department' in t ? t.department : undefined
          const { error } = await supabase.from('saved_tenders').insert({
            user_id: user.id,
            email,
            source_id: t.id,
            title: t.title,
            state: t.state,
            agency: dept,
            deadline: t.deadline,
            sector: 'sector' in t ? t.sector : undefined,
            source_url: 'sourceUrl' in t ? t.sourceUrl : undefined,
          })
          if (error) {
            setSavedIds(savedIds) // revert
            return currentlySaved
          }
        }
      } else {
        writeGuest([...next])
      }

      return !currentlySaved
    },
    [savedIds, user, email, supabase]
  )

  const value = useMemo<SavedState>(
    () => ({
      savedIds,
      isSaved: (id: string) => savedIds.has(id),
      toggleSaved,
      ready,
    }),
    [savedIds, toggleSaved, ready]
  )

  return <SavedContext.Provider value={value}>{children}</SavedContext.Provider>
}

export function useSaved() {
  return useContext(SavedContext)
}
