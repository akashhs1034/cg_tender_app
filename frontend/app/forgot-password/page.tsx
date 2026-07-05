'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Mail, ArrowLeft, CheckCircle2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { OpportaLogo } from '@/components/opporta-logo'
import { createClient } from '@/lib/supabase/client'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
      })
      if (error) {
        setError(error.message)
      } else {
        setSent(true)
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
        <Link href="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
          <span className="text-brand-blue font-semibold">Back to Sign In</span>
        </Link>
      </header>

      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="rounded-2xl border border-border-subtle bg-surface p-8 shadow-2xl shadow-black/40">
            {sent ? (
              <div className="text-center">
                <CheckCircle2 className="w-10 h-10 text-success mx-auto mb-3" />
                <h1 className="font-heading font-bold text-xl">Check your email</h1>
                <p className="text-sm text-text-secondary mt-2">
                  If an account exists for <span className="text-text-primary font-medium">{email}</span>,
                  we&apos;ve sent a link to reset your password. The link expires in 1 hour.
                </p>
                <Link href="/login" className="inline-flex items-center gap-1.5 text-sm text-brand-blue hover:underline mt-5">
                  <ArrowLeft className="w-4 h-4" /> Back to sign in
                </Link>
              </div>
            ) : (
              <>
                <div className="text-center mb-8">
                  <h1 className="font-heading font-bold text-2xl">Forgot your password?</h1>
                  <p className="text-sm text-text-secondary mt-1">
                    Enter your account email and we&apos;ll send you a reset link.
                  </p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2.5 text-xs text-danger">
                      <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}
                  <div>
                    <label htmlFor="email" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <input
                        id="email"
                        type="email"
                        required
                        autoComplete="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                      />
                    </div>
                  </div>
                  <Button type="submit" disabled={loading}
                    className="w-full h-11 font-semibold text-sm bg-brand-blue hover:bg-brand-blue/90 text-white">
                    {loading ? 'Sending…' : 'Send reset link'}
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
