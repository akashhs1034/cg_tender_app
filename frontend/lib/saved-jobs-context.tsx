'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/lib/auth-context'
import type { Job } from '@/lib/mock-data'

interface SavedJobsState {
  savedIds: Set<string>
  isSaved: (id: string) => boolean
  toggleSaved: (j: Job) => Promise<boolean>
  ready: boolean
}

const SavedJobsContext = createContext<SavedJobsState>({
  savedIds: new Set(),
  isSaved: () => false,
  toggleSaved: async () => false,
  ready: false,
})

const GUEST_KEY = 'opporta:saved-jobs'

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

export function SavedJobsProvider({ children }: { children: React.ReactNode }) {
  const supabase = useMemo(() => createClient(), [])
  const { user, email } = useAuth()
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let active = true
    setReady(false)
    async function load() {
      if (user && email) {
        const { data, error } = await supabase.from('saved_jobs').select('source_id').eq('email', email)
        if (!active) return
        if (error) setSavedIds(new Set(readGuest()))
        else setSavedIds(new Set((data ?? []).map((r) => r.source_id).filter(Boolean) as string[]))
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
    async (j: Job): Promise<boolean> => {
      const currentlySaved = savedIds.has(j.id)
      const next = new Set(savedIds)
      if (currentlySaved) next.delete(j.id)
      else next.add(j.id)
      setSavedIds(next)

      if (user && email) {
        if (currentlySaved) {
          const { error } = await supabase.from('saved_jobs').delete().eq('email', email).eq('source_id', j.id)
          if (error) {
            setSavedIds(savedIds)
            return currentlySaved
          }
        } else {
          const { error } = await supabase.from('saved_jobs').insert({
            user_id: user.id,
            email,
            source_id: j.id,
            title: j.title,
            department: j.department,
            state: j.state,
            deadline: j.deadline,
            apply_url: j.applyUrl,
          })
          if (error) {
            setSavedIds(savedIds)
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

  const value = useMemo<SavedJobsState>(
    () => ({ savedIds, isSaved: (id: string) => savedIds.has(id), toggleSaved, ready }),
    [savedIds, toggleSaved, ready]
  )

  return <SavedJobsContext.Provider value={value}>{children}</SavedJobsContext.Provider>
}

export function useSavedJobs() {
  return useContext(SavedJobsContext)
}
