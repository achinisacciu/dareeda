import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useUIStore, type ToastItem, type ToastVariant } from '@/stores/uiStore'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  ToastContainer.tsx                                                      ║
// ║                                                                          ║
// ║  Legge l'array `toasts` da uiStore e li mostra in un portal su body.    ║
// ║  Ogni toast si auto-rimuove dopo 4 s (gestito in uiStore.addToast).     ║
// ╚══════════════════════════════════════════════════════════════════════════╝

// ── Stili per variante ────────────────────────────────────────────────────────

const STYLES: Record<
  ToastVariant,
  { bg: string; border: string; icon: string; iconColor: string }
> = {
  success: {
    bg:        'bg-[--color-surface]',
    border:    'border-[--color-success]',
    icon:      '✓',
    iconColor: 'text-[--color-success]',
  },
  error: {
    bg:        'bg-[--color-surface]',
    border:    'border-[--color-error]',
    icon:      '✕',
    iconColor: 'text-[--color-error]',
  },
  warning: {
    bg:        'bg-[--color-surface]',
    border:    'border-[--color-warning]',
    icon:      '!',
    iconColor: 'text-[--color-warning]',
  },
  info: {
    bg:        'bg-[--color-surface]',
    border:    'border-[--color-primary]',
    icon:      'i',
    iconColor: 'text-[--color-primary]',
  },
}

// ── Singolo toast ─────────────────────────────────────────────────────────────

function ToastItemView({ item }: { item: ToastItem }) {
  const removeToast = useUIStore((s) => s.removeToast)
  const style = STYLES[item.variant] ?? STYLES.info

  return (
    <div
      role="alert"
      aria-live="polite"
      className={[
        'relative flex items-start gap-[--space-3]',
        'w-[320px] max-w-[calc(100vw-2rem)]',
        'px-[--space-4] py-[--space-3]',
        'rounded-[--radius-lg]',
        'border-l-4',
        'shadow-[var(--shadow-lg)]',
        'animate-[slideInRight_200ms_cubic-bezier(0.16,1,0.3,1)_forwards]',
        style.bg,
        style.border,
      ].join(' ')}
    >
      {/* Icona variante */}
      <span
        aria-hidden="true"
        className={[
          'shrink-0 mt-[2px]',
          'flex items-center justify-center',
          'w-5 h-5 rounded-full text-[10px] font-bold leading-none',
          style.iconColor,
        ].join(' ')}
      >
        {style.icon}
      </span>

      {/* Testo */}
      <div className="flex-1 min-w-0">
        <p className="text-[length:--text-sm] font-semibold text-[--color-text] leading-snug">
          {item.title}
        </p>
        {item.message && (
          <p className="mt-[--space-1] text-[length:--text-xs] text-[--color-text-muted] leading-normal">
            {item.message}
          </p>
        )}
      </div>

      {/* Chiudi */}
      <button
        type="button"
        aria-label="Chiudi notifica"
        onClick={() => removeToast(item.id)}
        className={[
          'shrink-0 mt-[1px]',
          'flex items-center justify-center',
          'w-5 h-5 rounded-[--radius-sm]',
          'text-[--color-text-faint] hover:text-[--color-text-muted]',
          'hover:bg-[--color-surface-offset]',
          'transition-[color,background] duration-[180ms]',
        ].join(' ')}
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
          <path d="M1 1l8 8M9 1L1 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  )
}

// ── Container ─────────────────────────────────────────────────────────────────

export function ToastContainer() {
  const toasts = useUIStore((s) => s.toasts)

  // Portale su document.body (evita z-index conflicts con modal/overlay)
  const portalTarget = useRef<HTMLElement | null>(null)
  if (typeof document !== 'undefined' && !portalTarget.current) {
    portalTarget.current = document.body
  }

  if (!portalTarget.current || toasts.length === 0) return null

  return createPortal(
    <div
      aria-label="Notifiche"
      className={[
        'fixed z-[9999]',
        'bottom-[--space-6] right-[--space-6]',
        'flex flex-col gap-[--space-2]',
        'pointer-events-none',
      ].join(' ')}
    >
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItemView item={t} />
        </div>
      ))}
    </div>,
    portalTarget.current,
  )
}

export default ToastContainer
