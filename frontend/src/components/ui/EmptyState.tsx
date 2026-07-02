import type { ReactNode } from 'react'
import { Button, type ButtonVariant } from './Button'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Types                                                                   ║
// ╚══════════════════════════════════════════════════════════════════════════╝

interface ActionDef {
  label:    string
  onClick:  () => void
  variant?: ButtonVariant
}

export interface EmptyStateProps {
  /** SVG icon o illustrazione */
  icon?:        ReactNode
  title:        string
  description?: string
  /** Azione primaria */
  action?:      ActionDef
  /** Azione secondaria */
  secondaryAction?: ActionDef
  /** Variante compatta (meno padding, testi più piccoli) */
  compact?:     boolean
  className?:   string
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Default icons                                                           ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export function IconEmptyFolder() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect x="4" y="14" width="40" height="28" rx="3" stroke="currentColor" strokeWidth="2" />
      <path d="M4 22h40" stroke="currentColor" strokeWidth="2" />
      <path d="M4 19a3 3 0 0 1 3-3h10l3 3H4Z" fill="currentColor" opacity=".15" />
      <path d="M20 33h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function IconEmptyChart() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect x="6" y="6" width="36" height="36" rx="4" stroke="currentColor" strokeWidth="2" />
      <path d="M14 34v-8M22 34v-14M30 34v-6M38 34v-18" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity=".35" />
      <path d="M14 26v8M22 20v14M30 28v6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

export function IconEmptySearch() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="20" cy="20" r="13" stroke="currentColor" strokeWidth="2" />
      <path d="m30 30 10 10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M15 20h10M20 15v10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity=".4" />
    </svg>
  )
}

export function IconEmptyReport() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path d="M28 6H12a2 2 0 0 0-2 2v32a2 2 0 0 0 2 2h24a2 2 0 0 0 2-2V16L28 6Z" stroke="currentColor" strokeWidth="2" />
      <path d="M28 6v10h10" stroke="currentColor" strokeWidth="2" />
      <path d="M16 26h16M16 32h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity=".4" />
    </svg>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Component                                                               ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Stato vuoto generico — usato quando non ci sono dati da mostrare.
 *
 * @example
 * // Nessun progetto
 * <EmptyState
 *   icon={<IconEmptyFolder />}
 *   title="Nessun progetto"
 *   description="Carica un file CSV o Parquet per iniziare."
 *   action={{ label: 'Carica dataset', onClick: () => setActivePage('upload') }}
 * />
 *
 * @example
 * // Analisi non ancora eseguita
 * <EmptyState
 *   icon={<IconEmptyChart />}
 *   title="Analisi non eseguita"
 *   description="Avvia l'analisi per esplorare il dataset."
 *   action={{ label: 'Avvia analisi', onClick: openRunModal, variant: 'primary' }}
 *   compact
 * />
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  compact   = false,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={[
        'flex flex-col items-center text-center',
        compact ? 'gap-[--space-3] py-[--space-8] px-[--space-4]' : 'gap-[--space-4] py-[--space-16] px-[--space-6]',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {/* Icon */}
      {icon && (
        <span
          className={[
            'flex items-center justify-center text-[--color-text-faint] transition-transform duration-180 hover:scale-105',
            compact ? 'mb-0' : 'mb-[--space-2]',
          ].join(' ')}
          aria-hidden="true"
        >
          {icon}
        </span>
      )}

      {/* Title */}
      <h3
        className={[
          'font-semibold text-[--color-text]',
          compact ? 'text-[length:--text-sm]' : 'text-[length:--text-base]',
        ].join(' ')}
      >
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p
          className={[
            'text-[--color-text-muted] max-w-[40ch] leading-relaxed',
            compact ? 'text-[length:--text-xs]' : 'text-[length:--text-sm]',
          ].join(' ')}
        >
          {description}
        </p>
      )}

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex items-center gap-[--space-2] mt-[--space-1] flex-wrap justify-center">
          {action && (
            <Button
              variant={action.variant ?? 'primary'}
              size={compact ? 'sm' : 'md'}
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              variant={secondaryAction.variant ?? 'ghost'}
              size={compact ? 'sm' : 'md'}
              onClick={secondaryAction.onClick}
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
