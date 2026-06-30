// Subtle 3D background layer for the main app surfaces. Kept deliberately faint so
// cards (opaque bg-surface) stay crisp and readable on top. Rendered by AppShell,
// so it never appears on the standalone login / signup / select-role pages.

const BACKGROUNDS = {
  global: '/bg-global.png',
  tenders: '/bg-tenders.png',
  jobs: '/bg-jobs.png',
} as const

export type BackgroundVariant = keyof typeof BACKGROUNDS

export function BackgroundShell({ variant = 'global' }: { variant?: BackgroundVariant }) {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* The 3D art, very low opacity for a premium, non-distracting texture */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-[0.06]"
        style={{ backgroundImage: `url(${BACKGROUNDS[variant]})` }}
      />
      {/* Soft scrim so content near the edges keeps strong contrast */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-transparent to-background/60" />
    </div>
  )
}
