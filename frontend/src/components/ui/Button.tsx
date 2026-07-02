import {
  forwardRef,
  type ButtonHTMLAttributes,
  type ReactNode,
} from 'react'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Button.tsx — design system coerente, micro-interazioni, a11y          ║
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

// ── Base classi ────────────────────────────────────────────────────────────────

const BASE =
  'inline-flex items-center justify-center gap-2 font-medium rounded-[--radius-md] ' +
  'border transition-all duration-180 ease-ui ' +
  'focus-visible:outline-2 focus-visible:outline-[--color-primary] focus-visible:outline-offset-2 ' +
  'select-none whitespace-nowrap ' +
  'active:scale-[0.97] ' +
  'disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100 ' +
  'min-h-[44px]' // touch target WCAG

const VARIANT: Record<ButtonVariant, string> = {
  primary:
    'bg-[--color-primary] border-[--color-primary] text-[--color-text-inverse] ' +
    'hover:bg-[--color-primary-hover] hover:border-[--color-primary-hover] hover:shadow-md ' +
    'active:bg-[--color-primary-active] active:border-[--color-primary-active] active:shadow-sm ' +
    'shadow-sm',

  secondary:
    'bg-[--color-surface-2] border-[--color-border] text-[--color-text] ' +
    'hover:bg-[--color-surface-offset] hover:border-[--color-border] hover:shadow-sm ' +
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
    'hover:bg-[--color-error-hover] hover:border-[--color-error-hover] hover:shadow-md ' +
    'active:opacity-90 active:shadow-sm ' +
    'shadow-sm',
}

const SIZE: Record<ButtonSize, string> = {
  sm: 'h-9  px-[--space-3] text-[length:--text-sm]  [&_svg]:size-3.5',
  md: 'h-10 px-[--space-4] text-[length:--text-sm]  [&_svg]:size-4',
  lg: 'h-11 px-[--space-6] text-[length:--text-base] [&_svg]:size-[18px]',
}

// ── Spinner ────────────────────────────────────────────────────────────────────

function Spinner({ size }: { size: ButtonSize }) {
  const dim = size === 'sm' ? 14 : size === 'md' ? 16 : 18
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

// ── Component ──────────────────────────────────────────────────────────────────

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