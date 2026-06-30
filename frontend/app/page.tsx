import Link from 'next/link'
import Image from 'next/image'
import {
  ArrowRight, FileText, Briefcase, Newspaper, Sparkles, Bell,
  CheckCircle2, Building2, BookOpen, Globe, Shield, TrendingUp,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { OpportaLogo } from '@/components/opporta-logo'
import { LanguageSwitcher } from '@/components/language-switcher'

const features = [
  {
    icon: Building2,
    title: 'For Contractors',
    description: 'Find tenders matching your trade, track deadlines, prepare bids with OPPORTA INTELLIGENCE, and never miss a valuable contract.',
    color: 'text-brand-blue', bg: 'bg-brand-blue/10', href: '/tenders', cta: 'Browse Tenders',
  },
  {
    icon: BookOpen,
    title: 'For Job Seekers',
    description: 'Discover job openings, check your profile match score, plan your exam preparation, and track application timelines.',
    color: 'text-[#6C3EF4]', bg: 'bg-[#6C3EF4]/10', href: '/jobs', cta: 'Browse Jobs',
  },
  {
    icon: Newspaper,
    title: 'Offline & Newspaper Coverage',
    description: 'We scan regional newspapers, district offices, and offline notice boards in CG and UP so you never miss a hidden opportunity.',
    color: 'text-success', bg: 'bg-success/10', href: '/tenders', cta: 'View All Sources',
  },
]

const aiFeatures = [
  { icon: Sparkles, title: 'OPPORTA INTELLIGENCE Match', description: 'OPPORTA INTELLIGENCE scores every tender and job against your profile — instant eligibility analysis, risk assessment, and recommended actions.' },
  { icon: FileText, title: 'Tender Bid Workspace', description: 'Generate bid checklists, identify missing documents, and draft bid files — all powered by OPPORTA INTELLIGENCE in one streamlined workspace.' },
  { icon: Briefcase, title: 'Exam Planner', description: 'Get a personalised preparation timeline, study checklists, and daily plans for every exam you track.' },
  { icon: Bell, title: 'Smart Alerts', description: 'Deadline reminders, corrigendum updates, new tenders matching your category — delivered before you even need to search.' },
]

const stats = [
  { value: '4,900+', label: 'Active Opportunities' },
  { value: 'CG + UP', label: 'States Covered' },
  { value: '312+', label: 'Offline Sources Tracked' },
  { value: 'Real-time', label: 'Update Frequency' },
]

export default function LandingPage() {
  return (
    <div className="bg-hero-3d min-h-screen text-text-primary font-sans">
      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-border-subtle bg-[#080E1D]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-5 py-3 flex items-center justify-between">
          <OpportaLogo iconSize="sm" />
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/dashboard" className="text-sm text-text-secondary hover:text-text-primary transition-colors">Dashboard</Link>
            <Link href="/tenders" className="text-sm text-text-secondary hover:text-text-primary transition-colors">Tenders</Link>
            <Link href="/jobs" className="text-sm text-text-secondary hover:text-text-primary transition-colors">Jobs</Link>
          </nav>
          <div className="flex items-center gap-2.5">
            <LanguageSwitcher />
            <Link href="/login">
              <Button size="sm" variant="outline" className="border-border-subtle text-text-secondary hover:text-text-primary hover:bg-surface-elevated font-semibold text-xs h-8">
                Sign In
              </Button>
            </Link>
            <Link href="/signup">
              <Button size="sm" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-xs h-8">
                Sign Up
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* 3D floating background visuals */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0" aria-hidden="true">
        {/* Tenders 3D — right side */}
        <div className="absolute -right-24 top-16 w-[480px] h-[480px] opacity-20">
          <Image
            src="/hero-tenders-3d.png"
            alt=""
            fill
            className="object-contain"
            priority
          />
        </div>
        {/* Jobs 3D — left side */}
        <div className="absolute -left-20 bottom-40 w-[400px] h-[400px] opacity-15">
          <Image
            src="/hero-jobs-3d.png"
            alt=""
            fill
            className="object-contain"
          />
        </div>
      </div>

      {/* Hero */}
      <section className="relative z-10 max-w-7xl mx-auto px-5 pt-20 pb-24 lg:pt-28 lg:pb-32 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-brand-blue/30 bg-brand-blue/10 text-xs font-semibold text-brand-blue mb-7">
          <Sparkles className="w-3 h-3" /> Chhattisgarh &amp; Uttar Pradesh — Powered by OPPORTA INTELLIGENCE
        </div>
        <h1 className="font-heading font-bold text-4xl sm:text-5xl lg:text-6xl xl:text-7xl text-balance leading-tight text-text-primary">
          Every<br />
          <span className="text-brand-blue">Opportunity.</span> One Platform.
        </h1>
        <p className="mt-6 text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed text-balance">
          Track tenders, jobs, notices, contracts, corrigendums, and upcoming opportunities across your target markets.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/select-role">
            <Button size="lg" className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold text-base px-8 gap-2 h-12">
              Get Started <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button size="lg" variant="outline" className="border-border-subtle bg-surface/50 text-text-primary hover:bg-surface-elevated font-semibold text-base px-8 h-12">
              View Live Opportunities
            </Button>
          </Link>
        </div>

        {/* Stats row */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
          {stats.map((s) => (
            <div key={s.label} className="rounded-xl border border-border-subtle bg-surface/60 px-4 py-4 text-center">
              <p className="font-heading font-bold text-xl text-text-primary">{s.value}</p>
              <p className="text-xs text-text-muted mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Feature cards */}
      <section className="relative z-10 max-w-7xl mx-auto px-5 pb-24">
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.title} className="rounded-2xl border border-border-subtle bg-surface p-7 flex flex-col hover:border-brand-blue/30 transition-all duration-200 group">
              <div className={`w-11 h-11 rounded-xl ${f.bg} flex items-center justify-center mb-5`}>
                <f.icon className={`w-5 h-5 ${f.color}`} />
              </div>
              <h3 className="font-heading font-bold text-lg text-text-primary mb-2">{f.title}</h3>
              <p className="text-sm text-text-secondary leading-relaxed flex-1">{f.description}</p>
              <Link href={f.href} className={`mt-5 inline-flex items-center gap-1.5 text-sm font-semibold ${f.color} group-hover:gap-2.5 transition-all`}>
                {f.cta} <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* OPPORTA INTELLIGENCE Features grid */}
      <section className="relative z-10 max-w-7xl mx-auto px-5 pb-24">
        <div className="rounded-2xl border border-border-subtle bg-surface overflow-hidden">
          <div className="px-7 py-8 border-b border-border-subtle">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#6C3EF4]/30 bg-[#6C3EF4]/10 text-xs font-semibold text-[#6C3EF4] mb-4">
              <Sparkles className="w-3 h-3" /> OPPORTA INTELLIGENCE
            </div>
            <h2 className="font-heading font-bold text-2xl lg:text-3xl text-text-primary">Built-in intelligence. Not bolted on.</h2>
            <p className="text-text-secondary mt-2 text-sm">OPPORTA INTELLIGENCE works quietly inside each opportunity, surfacing insights exactly when you need them.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 divide-border-subtle" style={{ borderTop: 'none' }}>
            {aiFeatures.map((f, i) => (
              <div key={f.title} className={`px-6 py-6 border-border-subtle ${i < 3 ? 'border-r' : ''} ${i >= 2 ? '' : 'border-b sm:border-b-0'}`}
                style={{ borderRight: i < 3 ? '1px solid rgba(255,255,255,0.08)' : 'none', borderBottom: i < 2 ? '1px solid rgba(255,255,255,0.08)' : 'none' }}>
                <div className="w-9 h-9 rounded-lg bg-[#6C3EF4]/10 flex items-center justify-center mb-4">
                  <f.icon className="w-4 h-4 text-[#6C3EF4]" />
                </div>
                <h4 className="font-heading font-semibold text-sm text-text-primary mb-1.5">{f.title}</h4>
                <p className="text-xs text-text-secondary leading-relaxed">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Alerts CTA banner */}
      <section className="relative z-10 max-w-7xl mx-auto px-5 pb-24">
        <div className="rounded-2xl border border-brand-blue/20 bg-brand-blue/5 px-7 py-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Bell className="w-4 h-4 text-brand-blue" />
              <span className="text-xs font-semibold text-brand-blue uppercase tracking-widest">Smart Alerts</span>
            </div>
            <h3 className="font-heading font-bold text-xl lg:text-2xl text-text-primary">Never miss a deadline again.</h3>
            <p className="text-text-secondary text-sm mt-1.5 max-w-md">
              Get notified of new tenders, job openings, and corrigendums matching your profile — across all sources.
            </p>
          </div>
          <Link href="/select-role">
            <Button className="bg-brand-blue hover:bg-brand-blue/90 text-white font-semibold px-7 h-11 gap-2 whitespace-nowrap">
              Enable Alerts <Bell className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Trust bar */}
      <section className="relative z-10 max-w-7xl mx-auto px-5 pb-16">
        <div className="flex flex-wrap items-center justify-center gap-6 md:gap-10">
          {[
            { icon: Shield, text: 'Verified Source Coverage' },
            { icon: TrendingUp, text: 'Real-time Updates' },
            { icon: Globe, text: 'CG & UP Coverage' },
            { icon: CheckCircle2, text: 'OPPORTA INTELLIGENCE' },
          ].map((t) => (
            <div key={t.text} className="flex items-center gap-2 text-text-muted">
              <t.icon className="w-4 h-4" />
              <span className="text-sm">{t.text}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border-subtle">
        <div className="max-w-7xl mx-auto px-5 py-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <OpportaLogo iconSize="sm" />
          <p className="text-xs text-text-muted">© 2025 OPPORTA. Opportunity Intelligence Platform.</p>
          <div className="flex items-center gap-4 text-xs text-text-muted">
            <Link href="/" className="hover:text-text-secondary transition-colors">Privacy</Link>
            <Link href="/" className="hover:text-text-secondary transition-colors">Terms</Link>
            <Link href="/" className="hover:text-text-secondary transition-colors">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
