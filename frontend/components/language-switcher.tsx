'use client'

import { useLanguage } from '@/lib/language-context'
import { cn } from '@/lib/utils'

interface LanguageSwitcherProps {
  className?: string
  /** compact: pill style with ENG/HIN labels only — for navbars */
  variant?: 'pill' | 'dropdown'
}

export function LanguageSwitcher({ className, variant = 'pill' }: LanguageSwitcherProps) {
  const { lang, setLang } = useLanguage()

  if (variant === 'pill') {
    return (
      <div
        className={cn(
          'flex items-center rounded-lg border border-border-subtle bg-surface-elevated p-0.5 gap-0.5',
          className
        )}
        role="group"
        aria-label="Select language"
      >
        <button
          onClick={() => setLang('en')}
          aria-pressed={lang === 'en'}
          className={cn(
            'px-2.5 py-1 rounded-md text-xs font-semibold transition-all duration-150',
            lang === 'en'
              ? 'bg-brand-blue text-white shadow-sm'
              : 'text-text-muted hover:text-text-secondary'
          )}
        >
          ENG
        </button>
        <button
          onClick={() => setLang('hi')}
          aria-pressed={lang === 'hi'}
          className={cn(
            'px-2.5 py-1 rounded-md text-xs font-semibold transition-all duration-150',
            lang === 'hi'
              ? 'bg-brand-blue text-white shadow-sm'
              : 'text-text-muted hover:text-text-secondary'
          )}
        >
          हिं
        </button>
      </div>
    )
  }

  // dropdown variant — for mobile drawers
  return (
    <select
      value={lang}
      onChange={(e) => setLang(e.target.value as 'en' | 'hi')}
      aria-label="Select language"
      className={cn(
        'px-3 py-1.5 rounded-lg border border-border-subtle bg-surface-elevated text-xs font-semibold text-text-secondary focus:outline-none focus:border-brand-blue transition-colors cursor-pointer',
        className
      )}
    >
      <option value="en">English</option>
      <option value="hi">हिंदी</option>
    </select>
  )
}
