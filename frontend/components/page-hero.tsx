import Image from 'next/image'
import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

export type HeroVariant = 'dashboard' | 'tenders' | 'jobs'

interface HeroConfig {
  img: string
  /** Rendered size of the 3D visual (px). */
  size: number
  mesh: string
  accent: string
  /** Soft radial glow behind the visual so darker assets (the seal) pop. */
  glow: string
}

// Each main surface gets its own 3D visual + accent glow. Assets live in
// /public and are referenced from the web root ("/logo-3d-seal.png", etc.).
const HERO: Record<HeroVariant, HeroConfig> = {
  dashboard: { img: '/logo-3d-seal.png', size: 140, mesh: 'bg-hero-3d', accent: 'text-brand-blue', glow: 'rgba(59,124,244,0.40)' },
  tenders: { img: '/hero-tenders-3d.png', size: 168, mesh: 'bg-mesh-tender', accent: 'text-brand-blue', glow: 'rgba(34,211,238,0.28)' },
  jobs: { img: '/hero-jobs-3d.png', size: 168, mesh: 'bg-mesh-job', accent: 'text-[#6C3EF4]', glow: 'rgba(108,62,244,0.30)' },
}

interface PageHeroProps {
  variant: HeroVariant
  title: string
  subtitle?: string
  /** Small label above the title (e.g. a section name). */
  eyebrow?: string
  icon?: ReactNode
  /** Optional actions row (links/buttons) under the subtitle. */
  children?: ReactNode
  className?: string
}

/**
 * Premium 3D brand/hero card shown at the top of the main app pages so the
 * OPPORTA 3D artwork is clearly visible after login without washing out the
 * whole page. The 3D visual sits on the right (a faint backdrop on mobile,
 * full strength on larger screens) while text stays fully readable on the left.
 */
export function PageHero({ variant, title, subtitle, eyebrow, icon, children, className }: PageHeroProps) {
  const cfg = HERO[variant]
  return (
    <div
      className={cn(
        'relative mb-6 overflow-hidden rounded-2xl border border-border-subtle p-5 sm:p-6',
        cfg.mesh,
        className,
      )}
    >
      {/* 3D visual — softer on mobile, full on sm+, with a glow so dark assets pop */}
      <div className="pointer-events-none absolute -right-3 top-1/2 flex -translate-y-1/2 select-none items-center justify-center opacity-60 sm:right-2 sm:opacity-100">
        <div
          className="absolute h-28 w-28 rounded-full blur-3xl sm:h-40 sm:w-40"
          style={{ background: cfg.glow }}
        />
        <Image
          src={cfg.img}
          alt=""
          aria-hidden
          width={cfg.size}
          height={cfg.size}
          priority
          className="relative object-contain drop-shadow-[0_12px_32px_rgba(0,0,0,0.55)]"
        />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-[80%] sm:max-w-[68%]">
        {eyebrow && (
          <div className={cn('mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-widest', cfg.accent)}>
            {icon}
            <span>{eyebrow}</span>
          </div>
        )}
        <h1 className="font-heading text-xl font-bold leading-tight text-text-primary text-balance sm:text-2xl">{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm leading-relaxed text-text-secondary">{subtitle}</p>}
        {children && <div className="mt-4 flex flex-wrap items-center gap-2">{children}</div>}
      </div>
    </div>
  )
}
