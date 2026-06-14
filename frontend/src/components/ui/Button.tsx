import {
  forwardRef,
  type ButtonHTMLAttributes,
  type ReactNode,
} from 'react'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Button.tsx                                                              ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
export type ButtonSize    = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:   ButtonVariant
  size?:      ButtonSize
  loading?:   boolean
  /** Icona (alias di iconLeft — prop più comune nel codebase) */
  icon?:      ReactNode
  iconLeft?:  ReactNode
  iconRight?: ReactNode
  fullWidth?: boolean
}

// ── Stili ─────────────────────────────────────────────────────────────────────

const BASE =
  'inline-flex items-center justify-center gap-2 font-medium rounded-[--radius-md] ' +
  'border transition-[color,background-color,border-color,box-shadow] duration-[180ms] ' +
  'focus-visible:outline-2 focus-visible:outline-[--color-primary] focus-visible:outline-offset-2 ' +
  'select-none whitespace-nowrap cursor-pointer disabled:opacity-50 disabled:pointer-events-none'

const VARIANT: Record<ButtonVariant, string> = {
  primary:
    'bg-[--color-primary] border-[--color-primary] text-[--color-text-inverse] ' +
    'hover:bg-[--color-primary-hover] hover:border-[--color-primary-hover] ' +
    'active:bg-[--color-primary-active] active:border-[--color-primary-active] ' +
    'shadow-[var(--shadow-sm)]',

  secondary:
    'bg-[--color-surface-2] border-[--color-border] text-[--color-text] ' +
    'hover:bg-[--color-surface-offset] hover:border-[--color-border] ' +
    'active:bg-[--color-surface-offset-2]',

  outline:
    'bg-transparent border-[--color-border] text-[--color-text] ' +
    'hover:bg-[--color-surface-offset] hover:border-[--color-primary] hover:text-[--color-primary] ' +
    'active:bg-[--color-primary-highlight]',

  ghost:
    'bg-transparent border-transparent text-[--color-text-muted] ' +
    'hover:bg-[--color-surface-offset] hover:text-[--color-text] ' +
    'active:bg-[--color-surface-offset-2]',

  danger:
    'bg-[--color-error] border-[--color-error] text-[--color-text-inverse] ' +
    'hover:bg-[--color-error-hover] hover:border-[--color-error-hover] ' +
    'active:opacity-90 ' +
    'shadow-[var(--shadow-sm)]',
}

const SIZE: Record<ButtonSize, string> = {
  sm: 'h-7  px-[--space-3] text-[length:--text-xs]  [&_svg]:size-3.5',
  md: 'h-9  px-[--space-4] text-[length:--text-sm]  [&_svg]:size-4',
  lg: 'h-11 px-[--space-6] text-[length:--text-base] [&_svg]:size-[18px]',
}

// ── Spinner ───────────────────────────────────────────────────────────────────

function Spinner({ size }: { size: ButtonSize }) {
  const dim = size === 'sm' ? 12 : size === 'md' ? 14 : 16
  return (
    <svg
      width={dim}
      height={dim}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className="animate-spin shrink-0"
    >
      <circle
        cx="12" cy="12" r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="32"
        strokeDashoffset="12"
        opacity="0.3"
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant   = 'secondary',
      size      = 'md',
      loading   = false,
      icon,
      iconLeft,
      iconRight,
      fullWidth = false,
      className = '',
      children,
      disabled,
      ...rest
    },
    ref,
  ) => {
    const isDisabled = disabled || loading
    // `icon` è alias di `iconLeft` — iconLeft ha precedenza se entrambi forniti
    const leadingIcon = iconLeft ?? icon

    const classes = [BASE, VARIANT[variant], SIZE[size], fullWidth ? 'w-full' : '', className]
      .filter(Boolean)
      .join(' ')

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        aria-busy={loading}
        className={classes}
        {...rest}
      >
        {loading ? (
          <Spinner size={size} />
        ) : (
          leadingIcon && (
            <span aria-hidden="true" className="shrink-0">{leadingIcon}</span>
          )
        )}

        {children && (
          <span className={loading ? 'opacity-70' : ''}>{children}</span>
        )}

        {!loading && iconRight && (
          <span aria-hidden="true" className="shrink-0">{iconRight}</span>
        )}
      </button>
    )
  },
)

Button.displayName = 'Button'
