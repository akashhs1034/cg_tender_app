'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'

interface AuthState {
  user: User | null
  loading: boolean
  /** Convenience: best-available display name for the current user. */
  displayName: string | null
  email: string | null
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  displayName: null,
  email: null,
  signOut: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const supabase = useMemo(() => createClient(), [])
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    supabase.auth
      .getUser()
      .then(({ data }) => {
        if (active) setUser(data.user ?? null)
      })
      .catch(() => {
        /* auth host unreachable — treat as signed out */
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => {
      active = false
      sub.subscription.unsubscribe()
    }
  }, [supabase])

  const value = useMemo<AuthState>(() => {
    const meta = (user?.user_metadata ?? {}) as Record<string, unknown>
    const displayName =
      (typeof meta.full_name === 'string' && meta.full_name) ||
      (typeof meta.name === 'string' && meta.name) ||
      user?.email?.split('@')[0] ||
      null
    return {
      user,
      loading,
      displayName,
      email: user?.email ?? null,
      signOut: async () => {
        await supabase.auth.signOut()
        setUser(null)
      },
    }
  }, [user, loading, supabase])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
