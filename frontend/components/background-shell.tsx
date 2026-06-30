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
    // Fixed to the viewport (-z-10) so the 3D art is a stable backdrop behind the
    // content on both mobile and desktop — it stays visible while the page scrolls,
    // instead of getting stretched far down a tall mobile page. Opaque cards keep
    // text crisp on top. Never mounted on the standalone login / signup pages.
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-[0.34] sm:opacity-[0.22]"
        style={{ backgroundImage: `url(${BACKGROUNDS[variant]})` }}
      />
      {/* Accent glow to give the backdrop depth without brightening the page */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_0%,rgba(59,124,244,0.10),transparent_60%)]" />
      {/* Soft scrim so cards and text stay readable while the 3D art shows through */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/10 via-background/30 to-background/70" />
    </div>
  )
}
