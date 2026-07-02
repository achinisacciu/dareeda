import React from 'react'
import { CheckCircle2, AlertTriangle, Fingerprint, Hash } from 'lucide-react'

interface KpiCard {
  label: string
  value: string
  icon: React.ReactNode
  variant?: 'success' | 'warning' | 'info' | 'default'
}

const iconColorMap: Record<string, string> = {
  success: 'text-[--color-success]',
  warning: 'text-amber-500',
  info:    'text-[--color-info]',
  default: 'text-[--color-tertiary-container]',
}

const badgeColorMap: Record<string, string> = {
  success: 'bg-[--color-success-light] text-[--color-success]',
  warning: 'bg-amber-100 text-amber-700',
  info:    'bg-[--color-info-light] text-[--color-info]',
  default: 'bg-[--color-tertiary]/10 text-[--color-tertiary-container]',
}

export function KpiCards() {
  const cards: KpiCard[] = [
    {
      label: 'Validità Schema',
      value: '100%',
      icon: <CheckCircle2 className="w-7 h-7" />,
      variant: 'success',
    },
    {
      label: 'Completezza',
      value: '—',
      icon: <AlertTriangle className="w-7 h-7" />,
      variant: 'warning',
    },
    {
      label: 'Unicità',
      value: '—',
      icon: <Fingerprint className="w-7 h-7" />,
      variant: 'default',
    },
    {
      label: 'Numeriche',
      value: '—',
      icon: <Hash className="w-7 h-7 text-blue-600" />,
      variant: 'info',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="
            bg-[--color-surface-glass]
            border border-[--color-outline-variant]
            rounded-[--radius-card] p-5 shadow-sm
            flex flex-col justify-between
            transition-all duration-180
            hover:shadow-md hover:-translate-y-0.5
          "
        >
          <div className="flex justify-between items-start mb-3">
            <div className={iconColorMap[c.variant ?? 'default']}>{c.icon}</div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${badgeColorMap[c.variant ?? 'default']}`}>
              {c.variant ?? 'info'}
            </span>
          </div>
          <div>
            <p className="text-[--color-on-surface-variant] text-xs font-medium uppercase tracking-wide">Schema</p>
            <h4 className="text-3xl font-bold font-headline mt-1 leading-none">{c.value}</h4>
          </div>
        </div>
      ))}
    </div>
  )
}