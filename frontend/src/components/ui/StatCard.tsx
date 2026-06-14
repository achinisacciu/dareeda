import type { ReactNode } from 'react'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  StatCard.tsx — KPI card glassmorphism / premium stats                  ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export type StatCardVariant = 'default' | 'success' | 'warning' | 'error' | 'info'

export interface StatCardProps {
  label: string
  value: ReactNode
  sublabel?: string
  variant?: StatCardVariant
  icon?: ReactNode
  trend?: { value: number; label?: string }
  className?: string
}

// ── Stili semantici ───────────────────────────────────────────────────────────

const VARIANT_STYLES: Record<
  StatCardVariant,
  {
    badge: string
    trend: string
    glow: string
    orbA: string
    orbB: string
    iconWrap: string
  }
> = {
  default: {
    badge: 'bg-[--color-info-highlight] text-[--color-text] border-[--color-border]',
    trend: 'text-[--color-text]',
    glow: 'shadow-[0_8px_32px_0_rgba(31,38,135,0.16)]',
    orbA: 'bg-[--color-primary]/20',
    orbB: 'bg-[--color-info]/16',
    iconWrap: 'bg-white/30 text-[--color-text]',
  },
  success: {
    badge: 'bg-[--color-success-highlight] text-[--color-success] border-[--color-success]/25',
    trend: 'text-[--color-success]',
    glow: 'shadow-[0_8px_32px_0_rgba(67,122,34,0.18)]',
    orbA: 'bg-[--color-success]/22',
    orbB: 'bg-[--color-primary]/14',
    iconWrap: 'bg-white/30 text-[--color-success]',
  },
  warning: {
    badge: 'bg-[--color-warning-highlight] text-[--color-warning] border-[--color-warning]/25',
    trend: 'text-[--color-warning]',
    glow: 'shadow-[0_8px_32px_0_rgba(150,66,25,0.18)]',
    orbA: 'bg-[--color-orange]/22',
    orbB: 'bg-[--color-warning]/16',
    iconWrap: 'bg-white/30 text-[--color-warning]',
  },
  error: {
    badge: 'bg-[--color-error-highlight] text-[--color-error] border-[--color-error]/25',
    trend: 'text-[--color-error]',
    glow: 'shadow-[0_8px_32px_0_rgba(161,44,123,0.18)]',
    orbA: 'bg-[--color-error]/20',
    orbB: 'bg-[--color-notification]/16',
    iconWrap: 'bg-white/30 text-[--color-error]',
  },
  info: {
    badge: 'bg-[--color-info-highlight] text-[--color-info] border-[--color-info]/25',
    trend: 'text-[--color-info]',
    glow: 'shadow-[0_8px_32px_0_rgba(0,100,148,0.18)]',
    orbA: 'bg-[--color-info]/22',
    orbB: 'bg-[--color-primary]/16',
    iconWrap: 'bg-white/30 text-[--color-info]',
  },
}

// ── Icone trend ───────────────────────────────────────────────────────────────

function TrendIcon({ value }: { value: number }) {
  if (value === 0) return null
  const up = value > 0

  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      aria-hidden="true"
      className={up ? 'text-[--color-success]' : 'text-[--color-error]'}
    >
      {up ? (
        <path d="M6 2L10 7H2L6 2Z" fill="currentColor" />
      ) : (
        <path d="M6 10L2 5H10L6 10Z" fill="currentColor" />
      )}
    </svg>
  )
}

// ── Component ────────────────────────────────────────────────────────────────

export function StatCard({
  label,
  value,
  sublabel,
  variant = 'default',
  icon,
  trend,
  className,
}: StatCardProps) {
  const s = VARIANT_STYLES[variant]
  const hasTrend = trend && trend.value !== 0

  return (
    <div
      className={[
        'relative overflow-hidden rounded-[24px]',
        'border border-white/35 dark:border-white/10',
        'bg-white/55 dark:bg-white/5',
        'backdrop-blur-xl',
        'p-[--space-4]',
        'min-h-[132px]',
        'transition-transform duration-200 ease-out',
        'hover:-translate-y-0.5',
        s.glow,
        className ?? '',
      ].join(' ')}
    >
      {/* Decorative blurred orbs */}
      <div
        aria-hidden="true"
        className={[
          'pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full blur-3xl',
          s.orbA,
        ].join(' ')}
      />
      <div
        aria-hidden="true"
        className={[
          'pointer-events-none absolute -left-10 -bottom-10 h-28 w-28 rounded-full blur-3xl',
          s.orbB,
        ].join(' ')}
      />

      <div className="relative z-10 flex h-full flex-col">
        {/* Top row */}
        <div className="mb-[--space-4] flex items-start justify-between gap-[--space-3]">
          <div
            className={[
              'rounded-[--radius-xl] border border-white/25 dark:border-white/10',
              'p-3 backdrop-blur-sm shadow-[var(--shadow-sm)]',
              s.iconWrap,
            ].join(' ')}
          >
            <span className="[&_svg]:size-5">
              {icon ?? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              )}
            </span>
          </div>

          {hasTrend ? (
            <span
              className={[
                'inline-flex items-center gap-1 rounded-full border px-[--space-3] py-1',
                'text-[length:--text-xs] font-bold backdrop-blur-sm',
                s.badge,
              ].join(' ')}
            >
              <TrendIcon value={trend.value} />
              <span>
                {trend.value > 0 ? '+' : ''}
                {trend.value}%
              </span>
            </span>
          ) : (
            <span
              className={[
                'inline-flex items-center rounded-full border px-[--space-3] py-1',
                'text-[length:--text-xs] font-bold backdrop-blur-sm',
                s.badge,
              ].join(' ')}
            >
              KPI
            </span>
          )}
        </div>

        {/* Label */}
        <p className="mb-1 text-[length:--text-xs] font-semibold uppercase tracking-[0.12em] text-[--color-text-muted]">
          {label}
        </p>

        {/* Main value */}
        <div className="text-[clamp(1.75rem,1.2rem+1.4vw,2.4rem)] font-black tracking-tight leading-none text-[--color-text] tabular-nums">
          {value}
        </div>

        {/* Footer */}
        <div className="mt-auto pt-[--space-3]">
          {sublabel ? (
            <p className="text-[length:--text-xs] font-medium text-[--color-text-muted]">
              {sublabel}
            </p>
          ) : trend?.label ? (
            <p className="text-[length:--text-xs] font-medium text-[--color-text-muted]">
              {trend.label}
            </p>
          ) : (
            <p className="text-[length:--text-xs] font-medium text-[--color-text-faint]">
              Dato aggiornato
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default StatCard