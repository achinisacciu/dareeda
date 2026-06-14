import React, { forwardRef, type HTMLAttributes, type KeyboardEvent, type ReactNode } from 'react'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Card.tsx                                                                ║
// ║  CardHeader accetta sia title (prop) che children (JSX)                 ║
// ║  CardBody accetta compact per padding ridotto                            ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?:     'default' | 'flat' | 'ghost'
  interactive?: boolean
  selected?:    boolean
  className?:   string
  children?:    ReactNode
}

export interface CardHeaderProps {
  title?:       string
  description?: string
  action?:      ReactNode
  className?:   string
  children?:    ReactNode
}

export interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
  children?:  ReactNode
  compact?:   boolean
}

export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  className?: string
  children?:  ReactNode
}

function buildCardClasses(
  variant: 'default' | 'flat' | 'ghost',
  interactive: boolean,
  selected: boolean,
  extra?: string,
): string {
  const base = 'relative rounded-[--radius-xl] transition-[box-shadow,border-color,background] duration-[180ms]'
  const variants = {
    default: [
      'bg-[--color-surface] border border-[--color-border]',
      interactive ? 'cursor-pointer hover:border-[--color-primary] hover:shadow-[var(--shadow-md)]' : '',
      selected ? 'border-[--color-primary] shadow-[var(--shadow-md)] bg-[--color-surface-2]' : 'shadow-[var(--shadow-sm)]',
    ].join(' '),
    flat: [
      'bg-[--color-surface-offset] border border-[--color-divider]',
      interactive ? 'cursor-pointer hover:bg-[--color-surface] hover:border-[--color-border]' : '',
      selected ? 'bg-[--color-surface] border-[--color-border]' : '',
    ].join(' '),
    ghost: [
      'bg-transparent border border-transparent',
      interactive ? 'cursor-pointer hover:bg-[--color-surface-offset] hover:border-[--color-divider]' : '',
      selected ? 'bg-[--color-surface-offset] border-[--color-divider]' : '',
    ].join(' '),
  }
  return [base, variants[variant], extra ?? ''].filter(Boolean).join(' ')
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', interactive = false, selected = false, className, children, onClick, onKeyDown, ...rest }, ref) => {
    const classes = buildCardClasses(variant, interactive, selected, className)

    function handleKeyDown(e: KeyboardEvent<HTMLDivElement>) {
      if (interactive && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault()
        onClick?.(e as unknown as React.MouseEvent<HTMLDivElement>)
      }
      onKeyDown?.(e)
    }

    return (
      <div
        ref={ref}
        className={classes}
        onClick={interactive ? onClick : undefined}
        onKeyDown={interactive ? handleKeyDown : onKeyDown}
        role={interactive ? 'button' : undefined}
        tabIndex={interactive ? 0 : undefined}
        aria-pressed={interactive && selected !== undefined ? selected : undefined}
        {...rest}
      >
        {children}
      </div>
    )
  },
)
Card.displayName = 'Card'

/**
 * CardHeader — accetta sia `title` prop che `children`.
 * Se entrambi presenti, `children` sovrascrive `title`.
 */
export function CardHeader({ title, description, action, className, children }: CardHeaderProps) {
  const heading = children ?? title
  return (
    <div className={['flex items-start justify-between gap-[--space-4] px-[--space-5] py-[--space-4]', className ?? ''].filter(Boolean).join(' ')}>
      <div className="min-w-0 flex-1">
        {heading && (
          <h3 className="text-[length:--text-sm] font-semibold text-[--color-text] leading-snug">
            {heading}
          </h3>
        )}
        {description && (
          <p className="mt-[--space-1] text-[length:--text-xs] text-[--color-text-muted] leading-normal">
            {description}
          </p>
        )}
      </div>
      {action && <div className="shrink-0 flex items-center gap-[--space-2]">{action}</div>}
    </div>
  )
}

export function CardBody({ className, children, compact, ...rest }: CardBodyProps) {
  return (
    <div
      className={[
        compact ? 'px-[--space-3] py-[--space-2]' : 'px-[--space-5] py-[--space-4]',
        className ?? '',
      ].filter(Boolean).join(' ')}
      {...rest}
    >
      {children}
    </div>
  )
}

export function CardFooter({ className, children, ...rest }: CardFooterProps) {
  return (
    <div
      className={['px-[--space-5] py-[--space-4] border-t border-[--color-divider]', className ?? ''].filter(Boolean).join(' ')}
      {...rest}
    >
      {children}
    </div>
  )
}
