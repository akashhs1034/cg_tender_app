'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import {
  Eye,
  EyeOff,
  Mail,
  Lock,
  User,
  Phone,
  ArrowRight,
  Building2,
  BookOpen,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { OpportaLogo } from '@/components/opporta-logo'
import { GoogleSignInButton } from '@/components/google-signin-button'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils'
import type { UserRole } from '@/lib/user-role'

const roles: Array<{
  value: UserRole
  label: string
  desc: string
  icon: React.ElementType
  selected: string
}> = [
  {
    value: 'contractor',
    label: 'Contractor / Business',
    desc: 'Tenders, bid preparation, corrigendums, and saved pipeline',
    icon: Building2,
    selected: 'bg-brand-blue/10 border-brand-blue/40 text-brand-blue',
  },
  {
    value: 'jobseeker',
    label: 'Job Seeker',
    desc: 'Government jobs, eligibility, deadlines, and exam preparation',
    icon: BookOpen,
    selected: 'bg-[#6C3EF4]/10 border-[#6C3EF4]/40 text-[#6C3EF4]',
  },
]

const states = ['Chhattisgarh', 'Uttar Pradesh', 'Both']

export default function SignupPage() {
  const router = useRouter()
  const [role, setRole] = useState<UserRole>('contractor')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    state: 'Chhattisgarh',
  })

  function handleChange(event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    setLoading(true)

    const statesOfInterest = form.state === 'Both'
      ? ['Chhattisgarh', 'Uttar Pradesh']
      : [form.state]

    try {
      const supabase = createClient()
      const { data, error: signUpError } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
        options: {
          data: {
            full_name: form.name,
            phone: form.phone,
            role,
            states_of_interest: statesOfInterest,
          },
        },
      })

      if (signUpError) {
        setError(signUpError.message)
        setLoading(false)
        return
      }

      if (data.session) {
        await supabase.from('profiles').upsert({
          email: form.email,
          full_name: form.name,
          states: statesOfInterest,
        })
        router.push('/dashboard')
        router.refresh()
        return
      }

      setNotice('Account created. Check your email to confirm your account, then sign in.')
      setLoading(false)
    } catch {
      setError('Could not reach the server. Please try again.')
      setLoading(false)
    }
  }

  const inputClass = 'w-full rounded-lg border border-border-subtle bg-surface-elevated px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-blue transition-colors'

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
        <Link href="/login" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
          Already have an account? <span className="text-brand-blue font-semibold">Sign in</span>
        </Link>
      </header>

      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-xl rounded-2xl border border-border-subtle bg-surface p-7 shadow-2xl shadow-black/40">
          <div className="text-center mb-6">
            <h1 className="font-heading font-bold text-2xl text-text-primary">Create your OPPORTA account</h1>
            <p className="text-sm text-text-secondary mt-1">Choose one experience. You can switch later from your profile.</p>
          </div>

          <GoogleSignInButton label="Continue with Google" />

          <div className="flex items-center gap-3 my-5">
            <span className="h-px flex-1 bg-border-subtle" />
            <span className="text-[11px] uppercase tracking-wider text-text-muted">or create with email</span>
            <span className="h-px flex-1 bg-border-subtle" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <p className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wide">I am using OPPORTA as</p>
              <div className="grid sm:grid-cols-2 gap-3">
                {roles.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setRole(option.value)}
                    className={cn(
                      'flex items-start gap-3 p-4 rounded-xl border text-left transition-all',
                      role === option.value
                        ? option.selected
                        : 'border-border-subtle bg-surface-elevated text-text-secondary hover:border-text-muted/40'
                    )}
                  >
                    <option.icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-text-primary">{option.label}</p>
                      <p className="text-xs text-text-muted mt-1 leading-relaxed">{option.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2.5 text-xs text-danger">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {notice && (
              <div className="flex items-start gap-2 rounded-lg border border-success/30 bg-success/10 px-3 py-2.5 text-xs text-success">
                <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                <span>{notice}</span>
              </div>
            )}

            <div className="grid sm:grid-cols-2 gap-4">
              <label className="block sm:col-span-2">
                <span className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Full Name</span>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input name="name" required value={form.name} onChange={handleChange} placeholder="Your name" className={`${inputClass} pl-9`} />
                </div>
              </label>

              <label className="block">
                <span className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Email</span>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input name="email" type="email" required autoComplete="email" value={form.email} onChange={handleChange} placeholder="you@example.com" className={`${inputClass} pl-9`} />
                </div>
              </label>

              <label className="block">
                <span className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Mobile Number</span>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input name="phone" type="tel" value={form.phone} onChange={handleChange} placeholder="+91 98765 43210" className={`${inputClass} pl-9`} />
                </div>
              </label>

              <label className="block">
                <span className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">State of Interest</span>
                <select name="state" value={form.state} onChange={handleChange} className={inputClass}>
                  {states.map((state) => <option key={state}>{state}</option>)}
                </select>
              </label>

              <label className="block">
                <span className="block text-xs font-semibold text-text-secondary mb-1.5 uppercase tracking-wide">Password</span>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={form.password}
                    onChange={handleChange}
                    placeholder="At least 8 characters"
                    className={`${inputClass} pl-9 pr-10`}
                  />
                  <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary" aria-label={showPassword ? 'Hide password' : 'Show password'}>
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </label>
            </div>

            <Button type="submit" disabled={loading} className="w-full h-11 font-semibold text-sm gap-2 bg-brand-blue hover:bg-brand-blue/90 text-white">
              {loading ? 'Creating account…' : 'Create account'} <ArrowRight className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </main>
    </div>
  )
}
