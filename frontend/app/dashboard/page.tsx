import Link from 'next/link'
import {
  FileText, Briefcase, Newspaper, RefreshCw, Clock, PlusCircle,
  MapPin, ArrowRight, Sparkles, TrendingUp, AlertTriangle,
} from 'lucide-react'
import { AppShell } from '@/components/app-shell'
import { StatCard } from '@/components/stat-card'
import { BadgeMode } from '@/components/ui/badge-mode'
import { AiMatchBadge } from '@/components/ui/ai-match-badge'
import { tenders, jobs, dashboardStats } from '@/lib/mock-data'

const statCards = [
  { label: 'Active Tenders', value: dashboardStats.activeTenders, icon: FileText, iconColor: 'text-brand-blue', iconBg: 'bg-brand-blue/10', trend: '+12 today', trendUp: true },
  { label: 'Active Jobs', value: dashboardStats.activeJobs, icon: Briefcase, iconColor: 'text-[#6C3EF4]', iconBg: 'bg-[#6C3EF4]/10', trend: '+8 today', trendUp: true },
  { label: 'Offline / Newspaper', value: dashboardStats.offlineNewspaper, icon: Newspaper, iconColor: 'text-success', iconBg: 'bg-success/10', trend: '+3 today', trendUp: true },
  { label: 'Corrigendums', value: dashboardStats.corrigendums, icon: RefreshCw, iconColor: 'text-warning', iconBg: 'bg-warning/10' },
  { label: 'Closing Soon', value: dashboardStats.closingSoon, icon: Clock, iconColor: 'text-danger', iconBg: 'bg-danger/10' },
  { label: 'New Today', value: dashboardStats.newToday, icon: PlusCircle, iconColor: 'text-brand-cyan', iconBg: 'bg-brand-cyan/10' },
]

const recommendedTenders = tenders.filter((t) => t.isRecommended).slice(0, 3)
const recommendedJobs = jobs.filter((j) => j.isRecommended).slice(0, 3)

export default function DashboardPage() {
  return (
    <AppShell pageTitle="Dashboard" pageSubtitle="Your opportunity overview">
      {/* Stat grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        {statCards.map((s) => (
          <StatCard key={s.label} label={s.label} value={s.value} icon={s.icon}
            iconColor={s.iconColor} iconBg={s.iconBg} trend={s.trend} trendUp={s.trendUp} />
        ))}
      </div>

      {/* CG / UP split */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="rounded-xl border border-border-subtle bg-surface p-5">
          <div className="flex items-center gap-2 mb-3">
            <MapPin className="w-4 h-4 text-brand-blue" />
            <span className="text-sm font-semibold text-text-primary">Chhattisgarh</span>
          </div>
          <p className="text-3xl font-heading font-bold text-text-primary">{dashboardStats.cgCount.toLocaleString()}</p>
          <p className="text-xs text-text-muted mt-1">Total active opportunities</p>
          <div className="mt-3 h-1.5 rounded-full bg-surface-elevated overflow-hidden">
            <div className="h-full bg-brand-blue rounded-full" style={{ width: `${(dashboardStats.cgCount / (dashboardStats.cgCount + dashboardStats.upCount) * 100).toFixed(0)}%` }} />
          </div>
          <p className="text-xs text-text-muted mt-1">{((dashboardStats.cgCount / (dashboardStats.cgCount + dashboardStats.upCount)) * 100).toFixed(0)}% of total</p>
        </div>
        <div className="rounded-xl border border-border-subtle bg-surface p-5">
          <div className="flex items-center gap-2 mb-3">
            <MapPin className="w-4 h-4 text-[#6C3EF4]" />
            <span className="text-sm font-semibold text-text-primary">Uttar Pradesh</span>
          </div>
          <p className="text-3xl font-heading font-bold text-text-primary">{dashboardStats.upCount.toLocaleString()}</p>
          <p className="text-xs text-text-muted mt-1">Total active opportunities</p>
          <div className="mt-3 h-1.5 rounded-full bg-surface-elevated overflow-hidden">
            <div className="h-full bg-[#6C3EF4] rounded-full" style={{ width: `${(dashboardStats.upCount / (dashboardStats.cgCount + dashboardStats.upCount) * 100).toFixed(0)}%` }} />
          </div>
          <p className="text-xs text-text-muted mt-1">{((dashboardStats.upCount / (dashboardStats.cgCount + dashboardStats.upCount)) * 100).toFixed(0)}% of total</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recommended Tenders */}
        <section className="rounded-2xl border border-border-subtle bg-surface overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-blue" />
              <h2 className="font-heading font-semibold text-sm text-text-primary">Recommended Tenders</h2>
            </div>
            <Link href="/tenders" className="text-xs font-medium text-brand-blue hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-border-subtle">
            {recommendedTenders.map((t) => (
              <Link key={t.id} href={`/tenders/${t.id}`} className="flex flex-col gap-2 px-5 py-4 hover:bg-surface-elevated transition-colors">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-text-primary leading-snug line-clamp-2">{t.title}</p>
                  <AiMatchBadge score={t.aiMatchScore} className="flex-shrink-0" />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <BadgeMode mode={t.mode} />
                  <span className="text-xs text-text-muted flex items-center gap-1"><MapPin className="w-3 h-3" />{t.district}, {t.state}</span>
                  <span className="text-xs text-text-muted flex items-center gap-1"><Clock className="w-3 h-3" />{t.deadline}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-text-secondary">
                  <span className="font-medium">{t.estimatedValue}</span>
                  <span className="text-text-muted">·</span>
                  <span className="truncate">{t.department}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Recommended Jobs */}
        <section className="rounded-2xl border border-border-subtle bg-surface overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#6C3EF4]" />
              <h2 className="font-heading font-semibold text-sm text-text-primary">Recommended Jobs</h2>
            </div>
            <Link href="/jobs" className="text-xs font-medium text-[#6C3EF4] hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-border-subtle">
            {recommendedJobs.map((j) => (
              <Link key={j.id} href={`/jobs/${j.id}`} className="flex flex-col gap-2 px-5 py-4 hover:bg-surface-elevated transition-colors">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-text-primary leading-snug line-clamp-2">{j.title}</p>
                  <AiMatchBadge score={j.matchScore} className="flex-shrink-0" />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <BadgeMode mode={j.mode} />
                  <span className="text-xs text-text-muted flex items-center gap-1"><MapPin className="w-3 h-3" />{j.district}, {j.state}</span>
                  <span className="text-xs text-text-muted flex items-center gap-1"><Clock className="w-3 h-3" />{j.deadline}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-text-secondary">
                  <span className="font-medium">{j.vacancies.toLocaleString()} vacancies</span>
                  <span className="text-text-muted">·</span>
                  <span className="truncate">{j.department}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>

      {/* Closing Soon Alert */}
      <div className="mt-6 rounded-xl border border-danger/20 bg-danger/5 px-5 py-4 flex items-start gap-3">
        <AlertTriangle className="w-4 h-4 text-danger mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-semibold text-text-primary">
            {dashboardStats.closingSoon} opportunities closing within 7 days
          </p>
          <p className="text-xs text-text-muted mt-0.5">
            Including {tenders.filter((t) => t.deadline.includes('Jul')).length} tenders and {jobs.filter((j) => j.deadline.includes('Jul')).length} jobs — review and act before deadlines pass.
          </p>
          <div className="flex gap-3 mt-2">
            <Link href="/tenders" className="text-xs font-semibold text-danger hover:underline">View urgent tenders</Link>
            <Link href="/jobs" className="text-xs font-semibold text-danger hover:underline">View urgent jobs</Link>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
