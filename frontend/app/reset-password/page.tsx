'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, LoaderCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { OpportaLogo } from '@/components/opporta-logo'
import { createClient } from '@/lib/supabase/client'

/**
 * Landing page for password-recovery links. It establishes the temporary
 * recovery session from PKCE, token-hash, implicit, or legacy callback flows,
 * then sets a new password with auth.updateUser.
 */
export default function ResetPasswordPage() {
  const router = useRouter()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [show, setShow] = useState(false)
  const [loading, setLoading] = useState(false)
  const [checkingLink, setCheckingLink] = useState(true)
  const [recoveryReady, setRecoveryReady] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const supabase = createClient()

    function finishWithSession() {
      if (!active) return
      setRecoveryReady(true)
      setError(null)
      setCheckingLink(false)

      // Remove one-time credentials from browser history after exchanging them.
      window.history.replaceState({}, '', '/reset-password')
    }

    async function establishRecoverySession() {
      const currentUrl = new URL(window.location.href)
      const hashParams = new URLSearchParams(currentUrl.hash.slice(1))
      const linkError =
        currentUrl.searchParams.get('error_description') ??
        currentUrl.searchParams.get('error') ??
        hashParams.get('error_description')

      if (linkError) {
        throw new Error(linkError)
      }

      const tokenHash = currentUrl.searchParams.get('token_hash')
      const code = currentUrl.searchParams.get('code')
      const accessToken = hashParams.get('access_token')
      const refreshToken = hashParams.get('refresh_token')

      if (tokenHash) {
        const { error: verifyError } = await supabase.auth.verifyOtp({
          token_hash: tokenHash,
          type: 'recovery',
        })
        if (verifyError) throw verifyError
        finishWithSession()
        return
      }

      if (code) {
        const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)
        if (!exchangeError) {
          finishWithSession()
          return
        }

        // createBrowserClient can exchange the code automatically before this
        // effect runs, so only fail if no session was created.
        const { data } = await supabase.auth.getSession()
        if (data.session) {
          finishWithSession()
          return
        }
        throw exchangeError
      }

      if (accessToken && refreshToken) {
        const { error: sessionError } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        })
        if (sessionError) throw sessionError
        finishWithSession()
        return
      }

      // Older links pass through /auth/callback, which exchanges the token
      // server-side and leaves the recovery session in cookies.
      const { data, error: sessionError } = await supabase.auth.getSession()
      if (sessionError) throw sessionError
      if (data.session) {
        finishWithSession()
        return
      }

      throw new Error('This reset link is invalid or expired. Please request a new one.')
    }

    const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
      if ((event === 'PASSWORD_RECOVERY' || event === 'SIGNED_IN') && session) {
        finishWithSession()
      }
    })

    establishRecoverySession().catch((reason: unknown) => {
      if (!active) return
      const message = reason instanceof Error ? reason.message : 'This reset link is invalid or expired.'
      setError(
        message.toLowerCase().includes('code verifier')
          ? 'This reset link was opened in a different browser. Please request a new link and open it in this browser.'
          : message
      )
      setRecoveryReady(false)
      setCheckingLink(false)
    })

    return () => {
      active = false
      authListener.subscription.unsubscribe()
    }
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!recoveryReady) {
      setError('Please open a valid password-reset link before setting a new password.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.updateUser({ password })
      if (error) {
        setError(
          error.message.toLowerCase().includes('session')
            ? 'This reset link has expired. Please request a new one from the Forgot Password page.'
            : error.message)
      } else {
        setDone(true)
        setTimeout(() => { router.push('/dashboard'); router.refresh() }, 1500)
      }
    } catch {
      setError('Could not reach the server. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-hero-3d min-h-screen flex flex-col text-text-primary font-sans">
      <header className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-border-subtle bg-[#080E1D]/70 backdrop-blur-md">
        <Link href="/"><OpportaLogo iconSize="sm" /></Link>
      </header>

      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="rounded-2xl border border-border-subtle bg-surface p-8 shadow-2xl shadow-black/40">
            {checkingLink ? (
              <div className="text-center py-4">
                <LoaderCircle className="w-9 h-9 text-brand-blue mx-auto mb-3 animate-spin" />
                <h1 className="font-heading font-bold text-xl">Verifying reset link</h1>
                <p className="text-sm text-text-secondary mt-2">This will only take a moment.</p>
              </div>
            ) : done ? (
              <div className="text-center">
                <CheckCircle2 className="w-10 h-10 text-success mx-auto mb-3" />
                <h1 className="font-heading font-bold text-xl">Password updated</h1>
                <p className="text-sm text-text-secondary mt-2">You&apos;re signed in — taking you to your dashboard…</p>
              </div>
            ) : !recoveryReady ? (
              <div className="text-center">
                <AlertCircle className="w-10 h-10 text-danger mx-auto mb-3" />
                <h1 className="font-heading font-bold text-xl">Reset link unavailable</h1>
                <p className="text-sm text-text-secondary mt-2">
                  {error ?? 'This reset link is invalid or expired.'}
                </p>
                <Link
                  href="/forgot-password"
                  className="inline-flex items-center text-sm text-brand-blue hover:underline mt-5"
                >
                  Request a new reset link
                </Link>
              </div>
            ) : (
              <>
                <div className="text-center mb-8">
                  <h1 className="font-heading font-bold text-2xl">Set a new password</h1>
                  <p className="text-sm text-text-secondary mt-1">Choose a strong password for your account.</p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2.5 text-xs text-danger">
                      <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}
                  <div>
                    <label htmlFor="password" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                      New password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <input
                        id="password"
                        type={show ? 'text' : 'password'}
                        required
                        minLength={8}
                        autoComplete="new-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="At least 8 characters"
                        className="w-full pl-9 pr-10 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                      />
                      <button type="button" onClick={() => setShow(!show)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
                        aria-label={show ? 'Hide password' : 'Show password'}>
                        {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label htmlFor="confirm" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                      Confirm password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <input
                        id="confirm"
                        type={show ? 'text' : 'password'}
                        required
                        minLength={8}
                        autoComplete="new-password"
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                        placeholder="Repeat the password"
                        className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                      />
                    </div>
                  </div>
                  <Button type="submit" disabled={loading}
                    className="w-full h-11 font-semibold text-sm bg-brand-blue hover:bg-brand-blue/90 text-white">
                    {loading ? 'Saving…' : 'Update password'}
                  </Button>
                </form>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
