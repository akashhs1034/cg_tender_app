'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Eye, EyeOff, Mail, Lock, ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { OpportaLogo } from '@/components/opporta-logo'
import { cn } from '@/lib/utils'

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      window.location.href = '/dashboard'
    }, 1200)
  }

  return (
    <div className="bg-hero-3d min-h-screen flex flex-col text-text-primary font-sans">
      {/* 3D background visuals */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0" aria-hidden="true">
        <div className="absolute -right-20 top-10 w-[420px] h-[420px] opacity-15">
          <Image src="/hero-tenders-3d.png" alt="" fill className="object-contain" />
        </div>
        <div className="absolute -left-16 bottom-20 w-[360px] h-[360px] opacity-10">
          <Image src="/hero-jobs-3d.png" alt="" fill className="object-contain" />
        </div>
      </div>

      {/* Topbar */}
      <header className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-border-subtle bg-[#080E1D]/70 backdrop-blur-md">
        <Link href="/">
          <OpportaLogo iconSize="sm" />
        </Link>
        <Link href="/signup" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
          Don&apos;t have an account? <span className="text-brand-blue font-semibold">Sign up</span>
        </Link>
      </header>

      {/* Main */}
      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          {/* Card */}
          <div className="rounded-2xl border border-border-subtle bg-surface p-8 shadow-2xl shadow-black/40">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-brand-blue/30 bg-brand-blue/10 text-xs font-semibold text-brand-blue mb-4">
                <Sparkles className="w-3 h-3" /> Powered by OPPORTA INTELLIGENCE
              </div>
              <h1 className="font-heading font-bold text-2xl text-text-primary">Welcome back</h1>
              <p className="text-sm text-text-secondary mt-1">Sign in to access your opportunities</p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
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

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="password" className="block text-xs font-semibold text-text-secondary uppercase tracking-wide">
                    Password
                  </label>
                  <Link href="/forgot-password" className="text-xs text-brand-blue hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full pl-9 pr-10 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Role selector */}
              <div>
                <label htmlFor="role" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                  I am a
                </label>
                <select
                  id="role"
                  className="w-full px-3 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary focus:outline-none focus:border-brand-blue transition-colors appearance-none cursor-pointer"
                >
                  <option value="contractor">Contractor / Bidder</option>
                  <option value="jobseeker">Job Seeker</option>
                  <option value="admin">Admin / Team Member</option>
                </select>
              </div>

              {/* Submit */}
              <Button
                type="submit"
                disabled={loading}
                className={cn(
                  'w-full h-11 font-semibold text-sm gap-2 mt-2',
                  'bg-brand-blue hover:bg-brand-blue/90 text-white',
                  loading && 'opacity-70 cursor-not-allowed'
                )}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  <>Sign In <ArrowRight className="w-4 h-4" /></>
                )}
              </Button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-3 my-6">
              <div className="flex-1 h-px bg-border-subtle" />
              <span className="text-xs text-text-muted">or continue as</span>
              <div className="flex-1 h-px bg-border-subtle" />
            </div>

            {/* Guest */}
            <Link href="/dashboard">
              <Button variant="outline" className="w-full h-10 text-sm border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated">
                Browse as Guest
              </Button>
            </Link>
          </div>

          {/* Sign up link */}
          <p className="text-center text-sm text-text-muted mt-6">
            New to OPPORTA?{' '}
            <Link href="/signup" className="text-brand-blue font-semibold hover:underline">
              Create a free account
            </Link>
          </p>
        </div>
      </main>
    </div>
  )
}
