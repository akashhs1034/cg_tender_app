import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  label: string
  value: string | number
  icon: LucideIcon
  iconColor?: string
  iconBg?: string
  trend?: string
  trendUp?: boolean
  className?: string
}

export function StatCard({
  label,
  value,
  icon: Icon,
  iconColor = 'text-brand-blue',
  iconBg = 'bg-brand-blue/10',
  trend,
  trendUp,
  className,
}: StatCardProps) {
  return (
    <div className={cn('rounded-xl border border-border-subtle bg-surface p-5 flex items-start gap-4', className)}>
      <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', iconBg)}>
        <Icon className={cn('w-5 h-5', iconColor)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-2xl font-heading font-bold text-text-primary tabular-nums">{typeof value === 'number' ? value.toLocaleString() : value}</p>
        <p className="text-sm text-text-muted mt-0.5">{label}</p>
        {trend && (
          <p className={cn('text-xs mt-1', trendUp ? 'text-success' : 'text-danger')}>
            {trendUp ? '+' : ''}{trend}
          </p>
        )}
      </div>
    </div>
  )
}
