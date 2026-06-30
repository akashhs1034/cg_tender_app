import { Wrench } from 'lucide-react'

/**
 * Labels a page that is still a UI demo (not yet backed by live data /
 * backend), so it reads as intentional rather than broken.
 */
export function DemoBanner({ children }: { children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex items-start gap-3 rounded-xl border border-warning/25 bg-warning/5 px-5 py-4">
      <Wrench className="w-4 h-4 text-warning mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-sm font-semibold text-text-primary">Preview feature</p>
        <p className="text-xs text-text-muted mt-0.5">
          {children ??
            'This screen is an interactive preview. It will connect to live data once the supporting backend is ready.'}
        </p>
      </div>
    </div>
  )
}
