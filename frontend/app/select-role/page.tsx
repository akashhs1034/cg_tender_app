'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Building2, BookOpen, ArrowRight, Zap, ChevronLeft, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/lib/auth-context'
import type { UserRole } from '@/lib/user-role'

const roles: Array<{
  id: UserRole
  title: string
  subtitle: string
  description: string
  icon: React.ElementType
  iconBg: string
  iconColor: string
  accent: string
  selectedBorder: string
  selectedBg: string
  highlights: string[]
}> = [
  {
    id: 'contractor',
    title: 'Contractor / Business',
    subtitle: 'Find and win tenders',
    description: 'A focused tender workspace for contractors, MSMEs, vendors, transporters, and service providers.',
    icon: Building2,
    iconBg: 'bg-brand-blue/10',
    iconColor: 'text-brand-blue',
    accent: 'hover:border-brand-blue/50 hover:bg-brand-blue/5',
    selectedBorder: 'border-brand-blue',
    selectedBg: 'bg-brand-blue/10',
    highlights: ['Tender matches and deadlines', 'Bid preparation workspace', 'Corrigendum and document tracking'],
  },
  {
    id: 'jobseeker',
    title: 'Job Seeker',
    subtitle: 'Find government jobs',
    description: 'A focused job and exam experience for candidates preparing for government recruitment.',
    icon: BookOpen,
    iconBg: 'bg-[#6C3EF4]/10',
    iconColor: 'text-[#6C3EF4]',
    accent: 'hover:border-[#6C3EF4]/50 hover:bg-[#6C3EF4]/5',
    selectedBorder: 'border-[#6C3EF4]',
    selectedBg: 'bg-[#6C3EF4]/10',
    highlights: ['Job matches and vacancies', 'Application deadline tracking', 'Exam planning and study guidance'],
  },
]

export default function SelectRolePage() {
  const router = useRouter()
  const { user, role } = useAuth()
  const [selected, setSelected] = useState<UserRole | null>(role)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const continueWithRole = async () => {
    if (!selected) return
    if (!user) {
      router.push('/signup')
      return
    }

    setSaving(true)
    setError(null)
    const supabase = createClient()
    const currentMeta = (user.user_metadata ?? {}) as Record<string, unknown>
    const { error: updateError } = await supabase.auth.updateUser({
      data: { ...currentMeta, role: selected },
    })

    if (updateError) {
      setError(updateError.message)
      setSaving(false)
      return
    }

    router.push('/dashboard')
    router.refresh()
  }

  return (
    <div className="min-h-screen bg-mesh-hero flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-brand-blue flex items-center justify-center">
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-heading font-bold text-base text-text-primary">OPPORTA</span>
        </div>
        <Link href={user ? '/profile' : '/'} className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-secondary transition-colors">
          <ChevronLeft className="w-4 h-4" /> Back
        </Link>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-5 py-12">
        <div className="text-center mb-9">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-blue mb-3">Personalise your workspace</p>
          <h1 className="font-heading font-bold text-3xl lg:text-4xl text-text-primary text-balance">
            What do you use OPPORTA for?
          </h1>
          <p className="mt-3 text-text-secondary text-base max-w-lg mx-auto">
            We will show only the tools and opportunities relevant to your work.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-5 w-full max-w-3xl">
          {roles.map((roleOption) => {
            const isSelected = selected === roleOption.id
            return (
              <button
                key={roleOption.id}
                onClick={() => setSelected(roleOption.id)}
                className={cn(
                  'text-left rounded-2xl border p-6 transition-all duration-200 cursor-pointer flex flex-col gap-4',
                  'border-border-subtle bg-surface',
                  roleOption.accent,
                  isSelected && `${roleOption.selectedBorder} ${roleOption.selectedBg}`
                )}
              >
                <div className="flex items-start justify-between">
                  <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center', roleOption.iconBg)}>
                    <roleOption.icon className={cn('w-5 h-5', roleOption.iconColor)} />
                  </div>
                  {isSelected && (
                    <div className="w-5 h-5 rounded-full bg-brand-blue flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </div>

                <div>
                  <p className="text-xs font-semibold text-text-muted mb-1">{roleOption.subtitle}</p>
                  <h2 className="font-heading font-bold text-lg text-text-primary">{roleOption.title}</h2>
                  <p className="text-sm text-text-secondary mt-1.5 leading-relaxed">{roleOption.description}</p>
                </div>

                <ul className="space-y-1.5">
                  {roleOption.highlights.map((highlight) => (
                    <li key={highlight} className="flex items-start gap-2 text-xs text-text-secondary">
                      <span className="w-1 h-1 rounded-full bg-text-muted mt-1.5 flex-shrink-0" />
                      {highlight}
                    </li>
                  ))}
                </ul>
              </button>
            )
          })}
        </div>

        {error && <p className="mt-5 text-sm text-danger">{error}</p>}

        <div className="mt-8 text-center">
          <button
            onClick={continueWithRole}
            disabled={!selected || saving}
            className="inline-flex items-center gap-2 bg-brand-blue hover:bg-brand-blue/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-8 h-12 rounded-lg transition-colors text-base"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
            {user ? 'Save and continue' : 'Continue to sign up'}
          </button>
          {user && role && (
            <p className="mt-3 text-xs text-text-muted">You can switch experiences again from your profile menu.</p>
          )}
        </div>
      </main>
    </div>
  )
}
