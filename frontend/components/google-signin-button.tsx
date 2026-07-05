'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { createClient } from '@/lib/supabase/client'

/** "Continue with Google" — Supabase OAuth (PKCE), lands on /auth/callback. */
export function GoogleSignInButton({ label = 'Continue with Google' }: { label?: string }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function signIn() {
    setLoading(true)
    setError(null)
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback?next=/dashboard`,
        },
      })
      if (error) {
        setError(error.message)
        setLoading(false)
      }
      // on success the browser navigates away to Google
    } catch {
      setError('Could not start Google sign-in. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div>
      <Button
        type="button"
        variant="outline"
        onClick={signIn}
        disabled={loading}
        className="w-full h-10 text-sm border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated gap-2"
      >
        {/* Google "G" mark */}
        <svg width="16" height="16" viewBox="0 0 48 48" aria-hidden="true">
          <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.2 6 29.3 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.3-.1-2.6-.4-3.9z"/>
          <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.2 6 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
          <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/>
          <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l6.2 5.2C40.9 35.6 44 30.3 44 24c0-1.3-.1-2.6-.4-3.9z"/>
        </svg>
        {loading ? 'Redirecting…' : label}
      </Button>
      {error && <p className="text-xs text-danger mt-2">{error}</p>}
    </div>
  )
}
