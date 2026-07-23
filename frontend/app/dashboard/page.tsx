import Link from 'next/link'
import { redirect } from 'next/navigation'
import {
  FileText,
  Briefcase,
  Newspaper,
  RefreshCw,
  Bookmark,
  User,
  MapPin,
  ArrowRight,
  Sparkles,
  Users,
  Target,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { PageHero } from '@/components/page-hero'
import { StatCard } from '@/components/stat-card'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { getTenders, getJobs, getDashboardStats } from '@/lib/data'
import { getCurrentUser } from '@/lib/supabase/server'
import { normalizeUserRole } from '@/lib/user-role'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const user = await getCurrentUser()
  if (!user) redirect('/login')

  const meta = (user.user_metadata ?? {}) as Record<string, unknown>
  const role = normalizeUserRole(meta.role)
  if (!role) redirect('/select-role')

  const firstName =
    (typeof meta.full_name === 'string' && meta.full_name.split(' ')[0]) ||
    user.email?.split('@')[0] ||
    'there'

  if (role === 'jobseeker') {
    const [jobs, dashboardStats] = await Promise.all([getJobs(), getDashboardStats()])
    const recommended = jobs.filter((job) => job.isRecommended)
    const recommendedJobs = (recommended.length ? recommended : jobs).slice(0, 6)
    const vacancies = jobs.reduce((sum, job) => sum + Math.max(0, job.vacancies), 0)
    const statesCovered = new Set(jobs.map((job) => job.state)).size

    const statCards = [
      { label: 'Active Jobs', value: dashboardStats.activeJobs, icon: Briefcase, iconColor: 'text-[#6C3EF4]', iconBg: 'bg-[#6C3EF4]/10' },
      { label: 'Recommended', value: recommended.length, icon: Target, iconColor: 'text-brand-blue', iconBg: 'bg-brand-blue/10' },
      { label: 'Vacancies', value: vacancies, icon: Users, iconColor: 'text-success', iconBg: 'bg-success/10' },
      { label: 'States Covered', value: statesCovered, icon: MapPin, iconColor: 'text-warning', iconBg: 'bg-warning/10' },
    ]

    return (
      <AppShell pageTitle="Job Seeker Home" pageSubtitle="Jobs, deadlines, and exam preparation in one place" bg="jobs">
        <PageHero
          variant="jobs"
          eyebrow="Your Job Workspace"
          icon={<Sparkles className="h-3.5 w-3.5" />}
          title={`Welcome back, ${firstName}`}
          subtitle="A focused view of government jobs matched to your profile across Chhattisgarh and Uttar Pradesh."
        >
          <Link href="/jobs" className="btn-glow inline-flex items-center gap-1.5 rounded-lg bg-[#6C3EF4] px-3.5 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#6C3EF4]/90">
            <Briefcase className="h-3.5 w-3.5" /> Browse Jobs
          </Link>
          <Link href="/profile" className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface/60 px-3.5 py-2 text-xs font-semibold text-text-secondary transition-colors hover:text-text-primary hover:bg-surface-elevated">
            <User className="h-3.5 w-3.5" /> Complete Profile
          </Link>
        </PageHero>

        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat) => (
            <StatCard key={stat.label} label={stat.label} value={stat.value} icon={stat.icon} iconColor={stat.iconColor} iconBg={stat.iconBg} />
          ))}
        </div>

        <section className="rounded-2xl border border-border-subtle bg-surface overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#6C3EF4]">Recommended for you</p>
              <h2 className="font-heading font-semibold text-base text-text-primary mt-1">Government jobs to review</h2>
            </div>
            <Link href="/jobs" className="text-xs font-medium text-[#6C3EF4] hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:[&>*:nth-child(odd)]:border-r divide-border-subtle">
            {recommendedJobs.map((job) => (
              <Link key={job.id} href={`/jobs/${job.id}`} className="flex flex-col gap-2 px-5 py-4 border-b border-border-subtle hover:bg-surface-elevated transition-colors">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-text-primary leading-snug line-clamp-2">{job.title}</p>
                  <AiMatchBadge score={job.matchScore} className="flex-shrink-0" />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <BadgeMode mode={job.mode} />
                  <span className="text-xs text-text-muted">{job.district}, {job.state}</span>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs text-text-secondary">
                  <span>{job.vacancies.toLocaleString()} vacancies</span>
                  <span className="text-text-muted">Deadline: {job.deadline}</span>
                </div>
              </Link>
            ))}
            {recommendedJobs.length === 0 && (
              <div className="md:col-span-2 px-5 py-12 text-center text-sm text-text-muted">
                No active jobs are available right now. Check again after the next data update.
              </div>
            )}
          </div>
        </section>
      </AppShell>
    )
  }

  const [tenders, dashboardStats] = await Promise.all([getTenders(), getDashboardStats()])
  const recommended = tenders.filter((tender) => tender.isRecommended)
  const recommendedTenders = (recommended.length ? recommended : tenders).slice(0, 6)

  const statCards = [
    { label: 'Active Tenders', value: dashboardStats.activeTenders, icon: FileText, iconColor: 'text-brand-blue', iconBg: 'bg-brand-blue/10' },
    { label: 'Recommended', value: recommended.length, icon: Target, iconColor: 'text-success', iconBg: 'bg-success/10' },
    { label: 'Offline / Newspaper', value: dashboardStats.offlineNewspaper, icon: Newspaper, iconColor: 'text-warning', iconBg: 'bg-warning/10' },
    { label: 'Corrigendums', value: dashboardStats.corrigendums, icon: RefreshCw, iconColor: 'text-danger', iconBg: 'bg-danger/10' },
  ]

  return (
    <AppShell pageTitle="Contractor Home" pageSubtitle="Tender discovery and bid preparation in one focused workspace" bg="tenders">
      <PageHero
        variant="tenders"
        eyebrow="Your Tender Workspace"
        icon={<Sparkles className="h-3.5 w-3.5" />}
        title={`Welcome back, ${firstName}`}
        subtitle="A focused view of tenders matched to your business across Chhattisgarh and Uttar Pradesh."
      >
        <Link href="/tenders" className="btn-glow inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-xs font-semibold text-white transition-colors hover:bg-brand-blue/90">
          <FileText className="h-3.5 w-3.5" /> Browse Tenders
        </Link>
        <Link href="/saved" className="inline-flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface/60 px-3.5 py-2 text-xs font-semibold text-text-secondary transition-colors hover:text-text-primary hover:bg-surface-elevated">
          <Bookmark className="h-3.5 w-3.5" /> Saved Pipeline
        </Link>
      </PageHero>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => (
          <StatCard key={stat.label} label={stat.label} value={stat.value} icon={stat.icon} iconColor={stat.iconColor} iconBg={stat.iconBg} />
        ))}
      </div>

      <section className="rounded-2xl border border-border-subtle bg-surface overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-brand-blue">Recommended for your business</p>
            <h2 className="font-heading font-semibold text-base text-text-primary mt-1">Tenders to review</h2>
          </div>
          <Link href="/tenders" className="text-xs font-medium text-brand-blue hover:underline flex items-center gap-1">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:[&>*:nth-child(odd)]:border-r divide-border-subtle">
          {recommendedTenders.map((tender) => (
            <Link key={tender.id} href={`/tenders/${tender.id}`} className="flex flex-col gap-2 px-5 py-4 border-b border-border-subtle hover:bg-surface-elevated transition-colors">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-text-primary leading-snug line-clamp-2">{tender.title}</p>
                <AiMatchBadge score={tender.aiMatchScore} className="flex-shrink-0" />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <BadgeMode mode={tender.mode} />
                <span className="text-xs text-text-muted">{tender.district}, {tender.state}</span>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-text-secondary">
                <span>{tender.estimatedValue}</span>
                <span className="text-text-muted">Deadline: {tender.deadline}</span>
              </div>
            </Link>
          ))}
          {recommendedTenders.length === 0 && (
            <div className="md:col-span-2 px-5 py-12 text-center text-sm text-text-muted">
              No active tenders are available right now. Check again after the next data update.
            </div>
          )}
        </div>
      </section>
    </AppShell>
  )
}
