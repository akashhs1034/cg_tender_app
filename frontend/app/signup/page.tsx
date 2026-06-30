'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import {
  Eye, EyeOff, Mail, Lock, User, Phone, ArrowRight,
  Building2, BookOpen, ShieldCheck, CheckCircle2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { OpportaLogo } from '@/components/opporta-logo'
import { cn } from '@/lib/utils'

type Role = 'contractor' | 'jobseeker' | 'admin'

const roles: { value: Role; label: string; desc: string; icon: React.ElementType; color: string; bg: string }[] = [
  {
    value: 'contractor',
    label: 'Contractor / Bidder',
    desc: 'Track tenders, prepare bids, manage projects',
    icon: Building2,
    color: 'text-brand-blue',
    bg: 'bg-brand-blue/10 border-brand-blue/30',
  },
  {
    value: 'jobseeker',
    label: 'Job Seeker',
    desc: 'Discover jobs, track exams, get match scores',
    icon: BookOpen,
    color: 'text-[#6C3EF4]',
    bg: 'bg-[#6C3EF4]/10 border-[#6C3EF4]/30',
  },
  {
    value: 'admin',
    label: 'Admin / Team',
    desc: 'Manage discovery queue and platform data',
    icon: ShieldCheck,
    color: 'text-success',
    bg: 'bg-success/10 border-success/30',
  },
]

const states = ['Chhattisgarh', 'Uttar Pradesh', 'Both']

export default function SignupPage() {
  const [step, setStep] = useState<1 | 2>(1)
  const [role, setRole] = useState<Role>('contractor')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    state: 'Chhattisgarh',
  })

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  function handleStep1(e: React.FormEvent) {
    e.preventDefault()
    setStep(2)
  }

  function handleStep2(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      window.location.href = '/dashboard'
    }, 1400)
  }

  return (
    <div className="bg-hero-3d min-h-screen flex flex-col text-text-primary font-sans">
      {/* 3D background */}
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
        <Link href="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
          Already have an account? <span className="text-brand-blue font-semibold">Sign in</span>
        </Link>
      </header>

      {/* Main */}
      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          {/* Progress */}
          <div className="flex items-center gap-2 mb-6 justify-center">
            {[1, 2].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border transition-colors',
                  step === s
                    ? 'bg-brand-blue border-brand-blue text-white'
                    : step > s
                    ? 'bg-success border-success text-white'
                    : 'bg-surface-elevated border-border-subtle text-text-muted'
                )}>
                  {step > s ? <CheckCircle2 className="w-4 h-4" /> : s}
                </div>
                {s < 2 && <div className={cn('w-16 h-px', step > s ? 'bg-success' : 'bg-border-subtle')} />}
              </div>
            ))}
          </div>

          {/* Card */}
          <div className="rounded-2xl border border-border-subtle bg-surface p-8 shadow-2xl shadow-black/40">
            {step === 1 ? (
              <>
                <div className="text-center mb-7">
                  <h1 className="font-heading font-bold text-2xl text-text-primary">Create your account</h1>
                  <p className="text-sm text-text-secondary mt-1">Step 1 of 2 — Choose your role</p>
                </div>

                {/* Role picker */}
                <div className="space-y-3 mb-6">
                  {roles.map((r) => (
                    <button
                      key={r.value}
                      type="button"
                      onClick={() => setRole(r.value)}
                      className={cn(
                        'w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left',
                        role === r.value
                          ? `${r.bg} ${r.color}`
                          : 'border-border-subtle bg-surface-elevated text-text-secondary hover:border-border-subtle/80'
                      )}
                    >
                      <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', role === r.value ? 'bg-white/10' : 'bg-surface')}>
                        <r.icon className={cn('w-5 h-5', role === r.value ? r.color : 'text-text-muted')} />
                      </div>
                      <div>
                        <p className={cn('text-sm font-semibold', role === r.value ? '' : 'text-text-primary')}>{r.label}</p>
                        <p className={cn('text-xs mt-0.5', role === r.value ? 'opacity-80' : 'text-text-muted')}>{r.desc}</p>
                      </div>
                      {role === r.value && (
                        <CheckCircle2 className={cn('w-4 h-4 ml-auto flex-shrink-0', r.color)} />
                      )}
                    </button>
                  ))}
                </div>

                {/* State */}
                <div className="mb-6">
                  <label htmlFor="state" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">
                    State of Interest
                  </label>
                  <select
                    id="state"
                    name="state"
                    value={form.state}
                    onChange={handleChange}
                    className="w-full px-3 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary focus:outline-none focus:border-brand-blue transition-colors appearance-none cursor-pointer"
                  >
                    {states.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <Button
                  onClick={() => setStep(2)}
                  className="w-full h-11 font-semibold text-sm gap-2 bg-brand-blue hover:bg-brand-blue/90 text-white"
                >
                  Continue <ArrowRight className="w-4 h-4" />
                </Button>
              </>
            ) : (
              <>
                <div className="text-center mb-7">
                  <h1 className="font-heading font-bold text-2xl text-text-primary">Your details</h1>
                  <p className="text-sm text-text-secondary mt-1">Step 2 of 2 — Account information</p>
                </div>

                <form onSubmit={handleStep2} className="space-y-4">
                  {/* Full name */}
                  <div>
                    <label htmlFor="name" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Full Name</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <input
                        id="name"
                        name="name"
                        type="text"
                        required
                        value={form.name}
                        onChange={handleChange}
                        placeholder="Rajesh Kumar"
                        className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label htmlFor="signup-email" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Email Address</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <input
                        id="signup-email"
                        name="email"
                        type="email"
                        required
                        autoComplete="email"
                        value={form.email}
                        onChange={handleChange}
                        placeholder="you@example.com"
                        className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                      />
                    </div>
                  </div>

                  {/* Phone */}
                  <div>
                    <label htmlFor="phone" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Mobile Number</label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <input
                        id="phone"
                        name="phone"
                        type="tel"
                        required
                        value={form.phone}
                        onChange={handleChange}
                        placeholder="+91 98765 43210"
                        className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-border-subtle bg-surface-elevated text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors"
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div>
                    <label htmlFor="signup-password" className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <input
                        id="signup-password"
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        minLength={8}
                        autoComplete="new-password"
                        value={form.password}
                        onChange={handleChange}
                        placeholder="At least 8 characters"
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

                  {/* Terms */}
                  <p className="text-xs text-text-muted">
                    By creating an account you agree to our{' '}
                    <Link href="/" className="text-brand-blue hover:underline">Terms of Service</Link>
                    {' '}and{' '}
                    <Link href="/" className="text-brand-blue hover:underline">Privacy Policy</Link>.
                  </p>

                  <div className="flex gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setStep(1)}
                      className="flex-1 h-11 text-sm border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated"
                    >
                      Back
                    </Button>
                    <Button
                      type="submit"
                      disabled={loading}
                      className={cn(
                        'flex-1 h-11 font-semibold text-sm gap-2',
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
                          Creating...
                        </span>
                      ) : (
                        <>Create Account <ArrowRight className="w-4 h-4" /></>
                      )}
                    </Button>
                  </div>
                </form>
              </>
            )}
          </div>

          <p className="text-center text-sm text-text-muted mt-6">
            Already have an account?{' '}
            <Link href="/login" className="text-brand-blue font-semibold hover:underline">Sign in</Link>
          </p>
        </div>
      </main>
    </div>
  )
}
