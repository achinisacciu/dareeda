import { type HTMLAttributes, type ReactNode } from 'react'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Types                                                                   ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export type BadgeVariant =
  | 'default'
  | 'primary'
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'purple'
  | 'orange'
  | 'muted'

export type BadgeSize = 'sm' | 'md'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?:  BadgeVariant
  size?:     BadgeSize
  /** Dot colorato a sinistra del testo */
  dot?:      boolean
  /** Icona a sinistra (sostituisce dot se entrambi presenti) */
  icon?:     ReactNode
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Style maps                                                              ║
// ╚══════════════════════════════════════════════════════════════════════════╝

const BASE =
  'inline-flex items-center gap-1.5 font-medium rounded-[--radius-full] ' +
  'border leading-none whitespace-nowrap'

const VARIANT: Record<BadgeVariant, { badge: string; dot: string }> = {
  default: {
    badge: 'bg-[--color-surface-offset] border-[--color-border] text-[--color-text-muted]',
    dot:   'bg-[--color-text-faint]',
  },
  muted: {
    badge: 'bg-[--color-surface-dynamic] border-transparent text-[--color-text-muted]',
    dot:   'bg-[--color-text-faint]',
  },
  primary: {
    badge: 'bg-[--color-primary-highlight] border-[--color-primary-highlight] text-[--color-primary]',
    dot:   'bg-[--color-primary]',
  },
  success: {
    badge: 'bg-[--color-success-highlight] border-[--color-success-highlight] text-[--color-success]',
    dot:   'bg-[--color-success]',
  },
  warning: {
    badge: 'bg-[--color-warning-highlight] border-[--color-warning-highlight] text-[--color-warning]',
    dot:   'bg-[--color-warning]',
  },
  error: {
    badge: 'bg-[--color-error-highlight] border-[--color-error-highlight] text-[--color-error]',
    dot:   'bg-[--color-error]',
  },
  info: {
    badge: 'bg-[--color-blue-highlight] border-[--color-blue-highlight] text-[--color-blue]',
    dot:   'bg-[--color-blue]',
  },
  purple: {
    badge: 'bg-[--color-purple-highlight] border-[--color-purple-highlight] text-[--color-purple]',
    dot:   'bg-[--color-purple]',
  },
  orange: {
    badge: 'bg-[--color-orange-highlight] border-[--color-orange-highlight] text-[--color-orange]',
    dot:   'bg-[--color-orange]',
  },
}

const SIZE: Record<BadgeSize, { badge: string; dot: string; icon: string }> = {
  sm: {
    badge: 'px-[--space-2] py-px text-[length:--text-xs]',
    dot:   'size-1.5',
    icon:  '[&_svg]:size-3',
  },
  md: {
    badge: 'px-[--space-3] py-[3px] text-[length:--text-xs]',
    dot:   'size-2',
    icon:  '[&_svg]:size-3.5',
  },
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Semantic type → badge variant mapping                                   ║
// ║  Usato nei componenti analisi per colorare i tipi di colonna             ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export const SEMANTIC_TYPE_VARIANT: Record<string, BadgeVariant> = {
  numeric_continuous:  'primary',
  numeric_discrete:    'info',
  categorical_nominal: 'orange',
  categorical_ordinal: 'warning',
  boolean:             'success',
  datetime:            'purple',
  text:                'muted',
  id:                  'default',
  geographic:          'success',
  unknown:             'default',
}

export const SEMANTIC_TYPE_LABEL: Record<string, string> = {
  numeric_continuous:  'Numerico continuo',
  numeric_discrete:    'Numerico discreto',
  categorical_nominal: 'Categorico nominale',
  categorical_ordinal: 'Categorico ordinale',
  boolean:             'Booleano',
  datetime:            'Datetime',
  text:                'Testo',
  id:                  'ID',
  geographic:          'Geografico',
  unknown:             'Sconosciuto',
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Component                                                               ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Badge / chip per label, stati, tipi semantici e metriche.
 *
 * @example
 * <Badge variant="success" dot>Completato</Badge>
 * <Badge variant="error" size="sm">Errore</Badge>
 * <Badge variant={SEMANTIC_TYPE_VARIANT[col.semantic_type]}>
 *   {SEMANTIC_TYPE_LABEL[col.semantic_type]}
 * </Badge>
 */
export function Badge({
  variant   = 'default',
  size      = 'md',
  dot       = false,
  icon,
  className = '',
  children,
  ...rest
}: BadgeProps) {
  const v = VARIANT[variant]
  const s = SIZE[size]

  const classes = [BASE, v.badge, s.badge, icon ? s.icon : '', className]
    .filter(Boolean)
    .join(' ')

  return (
    <span className={classes} {...rest}>
      {icon ? (
        <span aria-hidden="true" className="shrink-0 flex items-center">{icon}</span>
      ) : dot ? (
        <span
          aria-hidden="true"
          className={`shrink-0 rounded-full ${s.dot} ${v.dot}`}
        />
      ) : null}
      {children}
    </span>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  SemanticTypeBadge — shortcut per i tipi di colonna EDA                 ║
// ╚══════════════════════════════════════════════════════════════════════════╝

interface SemanticTypeBadgeProps {
  type:      string
  size?:     BadgeSize
  showDot?:  boolean
  className?: string
}

/**
 * Shortcut per mostrare il tipo semantico di una colonna EDA
 * con colore e label corretti in automatico.
 *
 * @example
 * <SemanticTypeBadge type="numeric_continuous" />
 * <SemanticTypeBadge type={col.semantic_type} size="sm" />
 */
export function SemanticTypeBadge({
  type,
  size     = 'sm',
  showDot  = false,
  className,
}: SemanticTypeBadgeProps) {
  return (
    <Badge
      variant={SEMANTIC_TYPE_VARIANT[type] ?? 'default'}
      size={size}
      dot={showDot}
      className={className}
    >
      {SEMANTIC_TYPE_LABEL[type] ?? type}
    </Badge>
  )
}
