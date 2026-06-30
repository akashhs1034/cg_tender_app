'use client'

import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CheckCircle2, Info, AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastVariant = 'success' | 'info' | 'error'

interface ToastItem {
  id: number
  title: string
  description?: string
  variant: ToastVariant
}

interface ToastOptions {
  description?: string
  /** Auto-dismiss delay in ms (default 2600). */
  duration?: number
}

interface ToastContextValue {
  toast: (title: string, variant?: ToastVariant, options?: ToastOptions) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const variantStyles: Record<ToastVariant, { icon: typeof CheckCircle2; ring: string; iconColor: string }> = {
  success: { icon: CheckCircle2, ring: 'border-success/30', iconColor: 'text-success' },
  info: { icon: Info, ring: 'border-brand-blue/30', iconColor: 'text-brand-blue' },
  error: { icon: AlertTriangle, ring: 'border-danger/30', iconColor: 'text-danger' },
}

let nextId = 1

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = useCallback(
    (title: string, variant: ToastVariant = 'success', options?: ToastOptions) => {
      const id = nextId++
      setToasts((prev) => [...prev, { id, title, variant, description: options?.description }])
      window.setTimeout(() => remove(id), options?.duration ?? 2600)
    },
    [remove],
  )

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Viewport — fixed above everything, bottom-center on mobile, bottom-right on desktop */}
      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[100] flex flex-col items-center gap-2 px-4 sm:inset-x-auto sm:right-5 sm:items-end">
        {toasts.map((t) => {
          const cfg = variantStyles[t.variant]
          const Icon = cfg.icon
          return (
            <div
              key={t.id}
              role="status"
              aria-live="polite"
              className={cn(
                'pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border bg-popover px-4 py-3 shadow-2xl shadow-black/40 backdrop-blur-sm',
                'animate-in fade-in slide-in-from-bottom-3 duration-200',
                cfg.ring,
              )}
            >
              <Icon className={cn('mt-0.5 h-4 w-4 flex-shrink-0', cfg.iconColor)} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-text-primary leading-snug">{t.title}</p>
                {t.description && <p className="mt-0.5 text-xs text-text-muted leading-snug">{t.description}</p>}
              </div>
              <button
                onClick={() => remove(t.id)}
                aria-label="Dismiss"
                className="flex-shrink-0 text-text-muted transition-colors hover:text-text-primary"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    // Safe no-op fallback so a stray call never crashes the page.
    return { toast: () => {} }
  }
  return ctx
}
