import { cn } from '@/lib/utils'
import { Sparkles } from 'lucide-react'

interface AiMatchBadgeProps {
  score: number
  className?: string
  showIcon?: boolean
}

function getScoreColor(score: number) {
  if (score >= 85) return 'text-success bg-success/10 border-success/25'
  if (score >= 65) return 'text-brand-blue bg-brand-blue/10 border-brand-blue/25'
  return 'text-warning bg-warning/10 border-warning/25'
}

export function AiMatchBadge({ score, className, showIcon = true }: AiMatchBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border',
        getScoreColor(score),
        className
      )}
    >
      {showIcon && <Sparkles className="w-2.5 h-2.5" />}
      {score}% match
    </span>
  )
}
