'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

export interface PageTab {
  label: string
  href: string
}

/**
 * Section tab switcher used to pair related surfaces:
 *   Tender Portal | Bid Documents   and   Government Jobs | Exam Planner
 * Active tab is derived from the current pathname.
 */
export function PageTabs({ tabs, accent = 'blue' }: { tabs: PageTab[]; accent?: 'blue' | 'purple' }) {
  const pathname = usePathname()
  const activeColor = accent === 'purple' ? 'border-[#6C3EF4] text-[#6C3EF4]' : 'border-brand-blue text-brand-blue'

  return (
    <div className="flex gap-1 mb-5 border-b border-border-subtle overflow-x-auto">
      {tabs.map((t) => {
        const active = pathname === t.href
        return (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              'px-4 py-2.5 text-sm font-semibold whitespace-nowrap border-b-2 -mb-px transition-colors',
              active ? activeColor : 'border-transparent text-text-muted hover:text-text-secondary'
            )}
          >
            {t.label}
          </Link>
        )
      })}
    </div>
  )
}
