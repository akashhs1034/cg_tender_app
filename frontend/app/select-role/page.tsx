'use client'

import Link from 'next/link'
import { Building2, BookOpen, ShieldAlert, ArrowRight, Zap, ChevronLeft } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

const roles = [
  {
    id: 'contractor',
    title: 'Contractor / Business',
    subtitle: 'Find tenders',
    description: 'Access tenders from official portals, departments, districts, newspapers, and discovered sources. Use Tender Intelligence inside each tender to bid smarter.',
    icon: Building2,
    iconBg: 'bg-brand-blue/10',
    iconColor: 'text-brand-blue',
    accent: 'hover:border-brand-blue/50 hover:bg-brand-blue/5',
    selectedBorder: 'border-brand-blue',
    selectedBg: 'bg-brand-blue/8',
    highlights: ['Tender search with AI match score', 'Bid workspace & checklist', 'Offline/newspaper tender tracking', 'Corrigendum alerts'],
    href: '/dashboard',
  },
  {
    id: 'jobseeker',
    title: 'Job Seeker',
    subtitle: 'Find jobs',
    description: 'Track job notifications, match your profile to vacancies, and plan your exam preparation from the job details page.',
    icon: BookOpen,
    iconBg: 'bg-[#6C3EF4]/10',
    iconColor: 'text-[#6C3EF4]',
    accent: 'hover:border-[#6C3EF4]/50 hover:bg-[#6C3EF4]/5',
    selectedBorder: 'border-[#6C3EF4]',
    selectedBg: 'bg-[#6C3EF4]/8',
    highlights: ['Profile match score for every job', 'Exam planner & study checklist', 'Salary & vacancy details', 'Application deadline alerts'],
    href: '/dashboard',
  },
  {
    id: 'admin',
    title: 'Admin',
    subtitle: 'Manage platform data',
    description: 'Review and approve auto-discovered opportunity sources, manage the content pipeline, and resolve CAPTCHA-required sources.',
    icon: ShieldAlert,
    iconBg: 'bg-danger/10',
    iconColor: 'text-danger',
    accent: 'hover:border-danger/40 hover:bg-danger/5',
    selectedBorder: 'border-danger',
    selectedBg: 'bg-danger/8',
    highlights: ['Discovery queue management', 'Source approval / rejection', 'CAPTCHA queue', 'Confidence scoring'],
    href: '/admin/discovery',
  },
]

export default function SelectRolePage() {
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-mesh-hero flex flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-brand-blue flex items-center justify-center">
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-heading font-bold text-base text-text-primary">OPPORTA</span>
        </div>
        <Link href="/" className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-secondary transition-colors">
          <ChevronLeft className="w-4 h-4" /> Back
        </Link>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center justify-center px-5 py-16">
        <div className="text-center mb-12">
          <h1 className="font-heading font-bold text-3xl lg:text-4xl text-text-primary text-balance">
            How are you using OPPORTA?
          </h1>
          <p className="mt-3 text-text-secondary text-base max-w-lg mx-auto">
            Choose your role to get a personalised experience tailored to your needs.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-5 w-full max-w-4xl">
          {roles.map((role) => {
            const isSelected = selected === role.id
            return (
              <button
                key={role.id}
                onClick={() => setSelected(role.id)}
                className={cn(
                  'text-left rounded-2xl border p-6 transition-all duration-200 cursor-pointer flex flex-col gap-4',
                  'border-border-subtle bg-surface',
                  role.accent,
                  isSelected && `${role.selectedBorder} ${role.selectedBg}`
                )}
              >
                <div className="flex items-start justify-between">
                  <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center', role.iconBg)}>
                    <role.icon className={cn('w-5 h-5', role.iconColor)} />
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
                  <p className="text-xs font-semibold text-text-muted mb-1">{role.subtitle}</p>
                  <h3 className="font-heading font-bold text-lg text-text-primary">{role.title}</h3>
                  <p className="text-sm text-text-secondary mt-1.5 leading-relaxed">{role.description}</p>
                </div>

                <ul className="space-y-1.5">
                  {role.highlights.map((h) => (
                    <li key={h} className="flex items-start gap-2 text-xs text-text-secondary">
                      <span className="w-1 h-1 rounded-full bg-text-muted mt-1.5 flex-shrink-0" />
                      {h}
                    </li>
                  ))}
                </ul>
              </button>
            )
          })}
        </div>

        {/* CTA */}
        <div className="mt-10">
          {selected ? (
            <Link href={roles.find((r) => r.id === selected)?.href ?? '/dashboard'}>
              <button className="inline-flex items-center gap-2 bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold px-8 h-12 rounded-lg transition-colors text-base">
                Continue as {roles.find((r) => r.id === selected)?.title} <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
          ) : (
            <p className="text-sm text-text-muted">Select a role above to continue</p>
          )}
        </div>
      </main>
    </div>
  )
}
