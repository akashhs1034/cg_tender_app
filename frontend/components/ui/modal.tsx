'use client'

import { useEffect, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  /** Optional small label shown above the title. */
  eyebrow?: string
  icon?: ReactNode
  /** Accent ring/glow colour for the header icon. */
  accent?: 'blue' | 'purple'
  children: ReactNode
  footer?: ReactNode
  className?: string
}

/**
 * Lightweight controlled dialog. Renders as a fixed overlay (z above the nav
 * and below toasts), closes on backdrop click or Escape, and locks body scroll
 * while open. No portal needed — fixed positioning escapes the layout flow.
 */
export function Modal({ open, onClose, title, eyebrow, icon, accent = 'blue', children, footer, className }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[90] flex items-end justify-center p-0 sm:items-center sm:p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
        onClick={onClose}
        aria-hidden
      />
      {/* Panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          'relative flex max-h-[88vh] w-full flex-col overflow-hidden rounded-t-2xl border border-border-subtle bg-surface shadow-2xl shadow-black/50',
          'animate-in fade-in zoom-in-95 slide-in-from-bottom-4 duration-200 sm:max-w-lg sm:rounded-2xl',
          className,
        )}
      >
        {/* Header */}
        <div className="flex items-start gap-3 border-b border-border-subtle px-5 py-4">
          {icon && (
            <div
              className={cn(
                'flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg',
                accent === 'purple' ? 'bg-[#6C3EF4]/10 text-[#6C3EF4]' : 'bg-brand-blue/10 text-brand-blue',
              )}
            >
              {icon}
            </div>
          )}
          <div className="min-w-0 flex-1">
            {eyebrow && (
              <p className={cn('text-[11px] font-semibold uppercase tracking-wide', accent === 'purple' ? 'text-[#6C3EF4]' : 'text-brand-blue')}>
                {eyebrow}
              </p>
            )}
            <h2 className="font-heading text-base font-bold text-text-primary leading-snug">{title}</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md text-text-muted transition-colors hover:bg-surface-elevated hover:text-text-primary"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>

        {/* Footer */}
        {footer && <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border-subtle px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}
