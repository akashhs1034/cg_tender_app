'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  User,
  ShieldAlert,
  Activity,
  Menu,
  X,
  Bell,
  ChevronDown,
  LogOut,
  Settings,
  Bookmark,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { OpportaLogo } from '@/components/opporta-logo'
import { LanguageSwitcher } from '@/components/language-switcher'
import { useToast } from '@/components/ui/toast'
import { useAuth } from '@/lib/auth-context'
import { useLanguage } from '@/lib/language-context'

const adminNavItems = [
  { tKey: 'admin_health', href: '/admin', icon: Activity },
  { tKey: 'admin_queue', href: '/admin/discovery', icon: ShieldAlert },
]

interface AppNavProps {
  isAdmin?: boolean
}

export function AppNav({ isAdmin = false }: AppNavProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const { toast } = useToast()
  const { user, displayName, email, role, signOut } = useAuth()
  const { t } = useLanguage()

  const navItems = user
    ? role === 'jobseeker'
      ? [
          { tKey: 'dashboard', href: '/dashboard', icon: LayoutDashboard },
          { tKey: 'jobs', href: '/jobs', icon: Briefcase },
          { tKey: 'saved', href: '/saved', icon: Bookmark },
          { tKey: 'profile', href: '/profile', icon: User },
        ]
      : role === 'contractor'
        ? [
            { tKey: 'dashboard', href: '/dashboard', icon: LayoutDashboard },
            { tKey: 'tenders', href: '/tenders', icon: FileText },
            { tKey: 'saved', href: '/saved', icon: Bookmark },
            { tKey: 'profile', href: '/profile', icon: User },
          ]
        : [
            { tKey: 'Choose experience', href: '/select-role', icon: User },
            { tKey: 'profile', href: '/profile', icon: User },
          ]
    : [
        { tKey: 'tenders', href: '/tenders', icon: FileText },
        { tKey: 'jobs', href: '/jobs', icon: Briefcase },
      ]

  const handleSignOut = async () => {
    setProfileOpen(false)
    await signOut()
    toast('Signed out', 'info')
    router.push('/login')
    router.refresh()
  }

  const navLink = (item: (typeof navItems)[number], mobile = false) => {
    const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={() => mobile && setMobileOpen(false)}
        className={cn(
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group',
          isActive
            ? 'bg-brand-blue/15 text-brand-blue'
            : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
        )}
      >
        <item.icon className={cn('w-4 h-4 flex-shrink-0', isActive ? 'text-brand-blue' : 'text-text-muted group-hover:text-text-secondary')} />
        {t(item.tKey)}
      </Link>
    )
  }

  return (
    <>
      <aside className="hidden lg:flex flex-col w-60 min-h-screen border-r border-border-subtle bg-[#0D1525] sticky top-0 h-screen">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
          <OpportaLogo iconSize="md" />
          <p className="text-[10px] text-text-muted leading-none">CG &amp; UP</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map((item) => navLink(item))}

          {isAdmin && (
            <>
              <div className="pt-3 pb-1 px-3">
                <p className="text-[10px] font-semibold text-text-muted uppercase tracking-widest">Admin</p>
              </div>
              {adminNavItems.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                      isActive
                        ? 'bg-danger/15 text-danger'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                    )}
                  >
                    <item.icon className="w-4 h-4 flex-shrink-0" />
                    {t(item.tKey)}
                  </Link>
                )
              })}
            </>
          )}
        </nav>

        <div className="px-4 py-3 border-t border-border-subtle flex items-center justify-between">
          <LanguageSwitcher />
          {!user && (
            <Link href="/login" className="text-xs font-semibold text-brand-blue hover:underline">{t('sign_in')}</Link>
          )}
        </div>

        {user && (
          <div className="px-3 py-3 border-t border-border-subtle">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-surface-elevated transition-all duration-150 text-left"
            >
              <div className="w-7 h-7 rounded-full bg-brand-blue/20 border border-brand-blue/30 flex items-center justify-center flex-shrink-0">
                <User className="w-3.5 h-3.5 text-brand-blue" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">{displayName ?? 'Account'}</p>
                <p className="text-xs text-text-muted truncate">{email}</p>
              </div>
              <ChevronDown className={cn('w-3.5 h-3.5 text-text-muted transition-transform', profileOpen && 'rotate-180')} />
            </button>
            {profileOpen && (
              <div className="mt-1 rounded-lg border border-border-subtle bg-popover overflow-hidden">
                <Link href="/profile" className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors">
                  <User className="w-3.5 h-3.5" /> {t('profile')}
                </Link>
                <Link href="/select-role" className="flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors">
                  <Settings className="w-3.5 h-3.5" /> Switch experience
                </Link>
                <button onClick={handleSignOut} className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-danger hover:bg-danger/10 transition-colors">
                  <LogOut className="w-3.5 h-3.5" /> {t('sign_out')}
                </button>
              </div>
            )}
          </div>
        )}
      </aside>

      <header className="lg:hidden sticky top-0 z-50 flex items-center justify-between px-4 py-3 bg-[#0D1525]/95 backdrop-blur-md border-b border-border-subtle">
        <OpportaLogo iconSize="md" />
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-elevated transition-colors relative" aria-label="Notifications">
            <Bell className="w-4 h-4 text-text-secondary" />
          </button>
          <button
            onClick={() => setMobileOpen(true)}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-elevated transition-colors"
            aria-label="Open navigation"
          >
            <Menu className="w-4 h-4 text-text-secondary" />
          </button>
        </div>
      </header>

      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-72 bg-[#0D1525] h-full flex flex-col border-r border-border-subtle">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
              <OpportaLogo iconSize="md" />
              <button onClick={() => setMobileOpen(false)} className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-elevated" aria-label="Close navigation">
                <X className="w-4 h-4 text-text-muted" />
              </button>
            </div>
            <div className="px-5 py-3 border-b border-border-subtle flex items-center justify-between">
              <LanguageSwitcher />
              {user ? (
                <button onClick={() => { setMobileOpen(false); handleSignOut() }} className="text-xs font-semibold text-danger border border-danger/30 px-2.5 py-1 rounded-lg hover:bg-danger/10 transition-colors">{t('sign_out')}</button>
              ) : (
                <Link href="/login" onClick={() => setMobileOpen(false)} className="text-xs font-semibold text-brand-blue">{t('sign_in')}</Link>
              )}
            </div>
            <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
              {navItems.map((item) => navLink(item, true))}
              {isAdmin && adminNavItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-all"
                >
                  <item.icon className="w-4 h-4 flex-shrink-0" />
                  {t(item.tKey)}
                </Link>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </>
  )
}
