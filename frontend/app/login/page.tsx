'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff, Mail, Lock, ArrowRight, Sparkles, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { OpportaLogo } from '@/components/opporta-logo'
import { GoogleSignInButton } from '@/components/google-signin-button'
import { createClient } from '@/lib/supabase/client'
import { normalizeUserRole } from '@/lib/user-role'

export default function LoginPage() {
  const router = useRouter()
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null
    return new URLSearchParams(window.location.search).get('error')
  })

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const supabase = createClient()
      const { data, error: signInError } = await supabase.auth.signInWithPassword({ email, password })
      if (signInError) {
        setError(signInError.message)
        setLoading(false)
        return
      }

      const role = normalizeUserRole(data.user?.user_metadata?.role)
      router.push(role ? '/dashboard' : '/select-role')
      router.refresh()
    } catch {
      setError('Could not reach the server. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="bg-hero-3d min-h-screen flex flex-col text-text-primary font-sans">
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0" aria-hidden="true">
        <div className="absolute -right-20 top-10 w-[420px] h-[420px] opacity-15">
          <Image src="/hero-tenders-3d.png" alt="" fill className="object-contain" />
        </div>
        <div className="absolute -left-16 bottom-20 w-[360px] h-[360px] opacity-10">
          <Image src="/hero-jobs-3d.png" alt="" fill className="object-contain" />
        </div>
      </div>

      <header className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-border-subtle bg-[#080E1D]/70 backdrop-blur-md">
        <Link href="/"><OpportaLogo iconSize="sm" /></Link>
        <Link href="/signup" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
          Don&apos;t have an account? <span className="text-brand-blue font-semibold">Sign up</span>
        </Link>
      </header>

      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-surface p-8 shadow-2xl shadow-black/40">
          <div className="text-center mb-7">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-brand-blue/30 bg-brand-blue/10 text-xs font-semibold text-brand-blue mb-4">
              <Sparkles className="w-3 h-3" /> Your personalised opportunity workspace
            </div>
            <h1 className="font-heading font-bold text-2xl text-text-primary">Welcome back</h1>
            <p className="text-sm text-text-secondary mt-1">Sign in and continue with your selected experience.</p>
          </div>

          <GoogleSignInButton />

          <div className="flex items-center gap-3 my-5">
            <span className="h-px flex-1 bg-border-subtle" />
            <span className="text-[11px] uppercase tracking-wider text-text-muted">or use email</span>
            <span className="h-px flex-1 bg-border-subtle" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2.5 text-xs text-danger">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="block text-xs font-semibold text-text-secondary uppercase tracking-wide">Password</label>
                <Link href="/forgot-password" className="text-xs text-brand-blue hover:underline">Forgot password?</Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-9 pr-10 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button type="submit" disabled={loading} className="w-full h-11 font-semibold text-sm gap-2 bg-brand-blue hover:bg-brand-blue/90 text-white">
              {loading ? 'Signing in…' : 'Sign in'} <ArrowRight className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </main>
    </div>
  )
}
