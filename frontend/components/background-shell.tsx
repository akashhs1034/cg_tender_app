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
      {/* Full-bleed 3D artwork covering the whole page. Cards sit on opaque
          bg-surface, so text stays crisp even with the art shown prominently. */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-90 sm:opacity-80"
        style={{ backgroundImage: `url(${BACKGROUNDS[variant]})` }}
      />
      {/* Accent glow for depth */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_0%,rgba(76,141,255,0.12),transparent_60%)]" />
      {/* Light scrim only at the very bottom so long pages fade into the base
          background while the artwork stays clearly visible up top. */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/15 to-background/60" />
    </div>
  )
}
