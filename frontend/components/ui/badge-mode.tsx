import { cn } from '@/lib/utils'
import type { TenderMode } from '@/lib/mock-data'

const modeConfig: Record<TenderMode, { label: string; classes: string }> = {
  Online: { label: 'Online', classes: 'bg-brand-blue/15 text-brand-blue border-brand-blue/25' },
  Offline: { label: 'Offline', classes: 'bg-warning/15 text-warning border-warning/25' },
  Newspaper: { label: 'Newspaper', classes: 'bg-success/15 text-success border-success/25' },
}

interface BadgeModeProps {
  mode: TenderMode
  className?: string
}

export function BadgeMode({ mode, className }: BadgeModeProps) {
  const config = modeConfig[mode]
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold border',
        config.classes,
        className
      )}
    >
      {config.label}
    </span>
  )
}
