'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  BarChart2,
  User,
  ExternalLink,
  ShieldAlert,
  Menu,
  X,
  Bell,
  ChevronDown,
  LogOut,
  Settings,
  Bookmark,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { OpportaLogo } from '@/components/opporta-logo'
import { LanguageSwitcher } from '@/components/language-switcher'
import { useToast } from '@/components/ui/toast'
import { useAuth } from '@/lib/auth-context'
import { useLanguage } from '@/lib/language-context'

const navItems = [
  { tKey: 'profile', href: '/profile', icon: User },
  { tKey: 'dashboard', href: '/dashboard', icon: LayoutDashboard },
  { tKey: 'jobs', href: '/jobs', icon: Briefcase },
  { tKey: 'tenders', href: '/tenders', icon: FileText },
  { tKey: 'saved', href: '/saved', icon: Bookmark },
  { tKey: 'analytics', href: '/analytics', icon: BarChart2 },
  { tKey: 'our_website', href: '/', icon: ExternalLink, external: true },
]

const adminNavItems = [
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
  const { user, displayName, email, signOut } = useAuth()
  const { t } = useLanguage()

  const handleSignOut = async () => {
    setProfileOpen(false)
    await signOut()
    toast('Signed out', 'info')
    router.push('/login')
    router.refresh()
  }

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-60 min-h-screen border-r border-border-subtle bg-[#0D1525] sticky top-0 h-screen">
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
          <OpportaLogo iconSize="sm" />
          <p className="text-[10px] text-text-muted leading-none">CG &amp; UP</p>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group',
                  isActive
                    ? 'bg-brand-blue/15 text-brand-blue'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                )}
              >
                <item.icon className={cn('w-4 h-4 flex-shrink-0', isActive ? 'text-brand-blue' : 'text-text-muted group-hover:text-text-secondary')} />
                {t(item.tKey)}
                {item.external && <ExternalLink className="w-3 h-3 ml-auto opacity-40" />}
              </Link>
            )
          })}

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

        {/* Language + Auth */}
        <div className="px-4 py-3 border-t border-border-subtle flex items-center justify-between">
          <LanguageSwitcher />
          {!user && (
            <Link href="/login" className="text-xs font-semibold text-brand-blue hover:underline">{t('sign_in')}</Link>
          )}
        </div>

        {/* Profile Section — only when signed in */}
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
                <button
                  onClick={() => { setProfileOpen(false); toast('Settings — coming soon', 'info', { description: 'Account settings connect after backend integration.' }) }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
                >
                  <Settings className="w-3.5 h-3.5" /> {t('settings')}
                </button>
                <button onClick={handleSignOut} className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-danger hover:bg-danger/10 transition-colors">
                  <LogOut className="w-3.5 h-3.5" /> {t('sign_out')}
                </button>
              </div>
            )}
          </div>
        )}
      </aside>

      {/* Mobile Topbar */}
      <header className="lg:hidden sticky top-0 z-50 flex items-center justify-between px-4 py-3 bg-[#0D1525]/95 backdrop-blur-md border-b border-border-subtle">
        <OpportaLogo iconSize="sm" />
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-elevated transition-colors relative">
            <Bell className="w-4 h-4 text-text-secondary" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-brand-blue" />
          </button>
          {!user && (
            <Link
              href="/login"
              className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-lg border border-border-subtle text-xs font-semibold text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
            >
              Sign In
            </Link>
          )}
          <button
            onClick={() => setMobileOpen(true)}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-elevated transition-colors"
          >
            <Menu className="w-4 h-4 text-text-secondary" />
          </button>
        </div>
      </header>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-72 bg-[#0D1525] h-full flex flex-col border-r border-border-subtle">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
              <OpportaLogo iconSize="sm" />
              <button onClick={() => setMobileOpen(false)} className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-elevated">
                <X className="w-4 h-4 text-text-muted" />
              </button>
            </div>
            {/* Language + auth in drawer */}
            <div className="px-5 py-3 border-b border-border-subtle flex items-center justify-between">
              <LanguageSwitcher />
              {user ? (
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs text-text-muted truncate max-w-[110px]">{email}</span>
                  <button onClick={() => { setMobileOpen(false); handleSignOut() }} className="text-xs font-semibold text-danger border border-danger/30 px-2.5 py-1 rounded-lg hover:bg-danger/10 transition-colors">{t('sign_out')}</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link href="/login" onClick={() => setMobileOpen(false)} className="text-xs font-semibold text-text-secondary border border-border-subtle px-2.5 py-1 rounded-lg hover:text-text-primary hover:bg-surface-elevated transition-colors">{t('sign_in')}</Link>
                  <Link href="/signup" onClick={() => setMobileOpen(false)} className="text-xs font-semibold text-white bg-brand-blue px-2.5 py-1 rounded-lg hover:bg-brand-blue/90 transition-colors">Sign Up</Link>
                </div>
              )}
            </div>
            <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
              {navItems.map((item) => {
                const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                      isActive ? 'bg-brand-blue/15 text-brand-blue' : 'text-text-secondary hover:text-text-primary hover:bg-surface-elevated'
                    )}
                  >
                    <item.icon className="w-4 h-4 flex-shrink-0" />
                    {t(item.tKey)}
                  </Link>
                )
              })}
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
