'use client'

import { AppNav } from '@/components/app-nav'
import { BackgroundShell, type BackgroundVariant } from '@/components/background-shell'
import { Bell, Search } from 'lucide-react'

interface AppShellProps {
  children: React.ReactNode
  isAdmin?: boolean
  pageTitle?: string
  pageSubtitle?: string
  /** Which subtle 3D background to show behind the page content. */
  bg?: BackgroundVariant
}

export function AppShell({ children, isAdmin = false, pageTitle, pageSubtitle, bg = 'global' }: AppShellProps) {
  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-background">
      <BackgroundShell variant={bg} />
      <AppNav isAdmin={isAdmin} />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Page Header (desktop) */}
        {(pageTitle) && (
          <div className="hidden lg:flex items-center justify-between px-8 pt-7 pb-5 border-b border-border-subtle">
            <div>
              <h1 className="font-heading font-bold text-2xl text-text-primary">{pageTitle}</h1>
              {pageSubtitle && <p className="text-sm text-text-muted mt-0.5">{pageSubtitle}</p>}
            </div>
            <div className="flex items-center gap-3">
              <button className="w-9 h-9 flex items-center justify-center rounded-lg border border-border-subtle hover:bg-surface-elevated transition-colors relative">
                <Bell className="w-4 h-4 text-text-secondary" />
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-brand-blue" />
              </button>
            </div>
          </div>
        )}
        <main className="relative flex-1 px-4 py-6 lg:px-8 lg:py-7">
          <div className="relative z-10">
            {/* Page header (mobile) — the desktop header above is hidden on small screens */}
            {pageTitle && (
              <div className="lg:hidden mb-4">
                <h1 className="font-heading font-bold text-xl text-text-primary leading-tight">{pageTitle}</h1>
                {pageSubtitle && <p className="text-[13px] text-text-muted mt-0.5">{pageSubtitle}</p>}
              </div>
            )}
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
