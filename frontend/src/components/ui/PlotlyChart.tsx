import { useEffect, useRef, useCallback, useState, memo } from 'react'
import type { Config, Data, Layout } from 'plotly.js'
import { useUIStore, selectThemeResolved } from '@/stores/uiStore'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Types                                                                   ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/** Shape del JSON restituito dal backend via _fig(fig) → fig.to_json() */
export interface PlotlyFigure {
  data:    Record<string, unknown>[]
  layout:  Record<string, unknown>
  config?: Record<string, unknown>
}

export interface PlotlyChartProps {
  figure:     PlotlyFigure | null | undefined
  /** Altezza fissa in px. Default: 320 */
  height?:    number
  /** Titolo accessibile per screen reader */
  title?:     string
  className?: string
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  CSS variable resolver                                                   ║
// ╚══════════════════════════════════════════════════════════════════════════╝

function cssVar(name: string, fallback = ''): string {
  if (typeof window === 'undefined') return fallback
  return (
    getComputedStyle(document.documentElement)
      .getPropertyValue(name)
      .trim() || fallback
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Theme layout overrides                                                  ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Sovrascrive i colori hardcoded del backend (paper/plot_bgcolor, font, grids)
 * con i valori del design system corrente (light / dark).
 *
 * Il backend genera sempre layout con:
 *   plot_bgcolor: "#F5F5F5" / paper_bgcolor: "#FFFFFF"
 *   font.family:  "JetBrains Mono"
 * Li rimpiazziamo con i CSS token del tema attivo.
 */
function buildLayoutOverrides(): Record<string, unknown> {
  const surface   = cssVar('--color-surface',        '#ffffff')
  const surfaceOff = cssVar('--color-surface-offset', '#f5f5f5')
  const textMuted = cssVar('--color-text-muted',      '#666666')
  const divider   = cssVar('--color-divider',         '#e0e0e0')
  const border    = cssVar('--color-border',          '#cccccc')
  const fontBody  = cssVar('--font-body',             'JetBrains Mono, monospace')

  const axisDefaults = {
    gridcolor:     divider,
    linecolor:     border,
    zerolinecolor: border,
    tickfont:      { color: textMuted, family: fontBody, size: 10 },
    title:         { font: { color: textMuted, family: fontBody, size: 11 } },
  }

  return {
    paper_bgcolor: surface,
    plot_bgcolor:  surfaceOff,
    font: {
      family: fontBody,
      color:  textMuted,
      size:   11,
    },
    title: {
      font: { family: fontBody, color: cssVar('--color-text', '#111111'), size: 13 },
      pad:  { t: 4, b: 4 },
    },
    margin:  { t: 48, b: 48, l: 60, r: 24 },
    xaxis:   axisDefaults,
    yaxis:   axisDefaults,
    yaxis2:  axisDefaults,
    legend:  {
      bgcolor:     'rgba(0,0,0,0)',
      font:        { color: textMuted, family: fontBody, size: 10 },
      borderwidth: 0,
    },
    hoverlabel: {
      bgcolor:    surface,
      bordercolor: border,
      font:       { family: fontBody, size: 11, color: cssVar('--color-text', '#111') },
    },
    modebar: { bgcolor: 'rgba(0,0,0,0)', color: textMuted },
  }
}

const PLOTLY_CONFIG: Record<string, unknown> = {
  responsive:      true,
  displayModeBar:  'hover',
  displaylogo:     false,
  modeBarButtonsToRemove: [
    'sendDataToCloud', 'editInChartStudio',
    'lasso2d', 'select2d',
  ],
  toImageButtonOptions: { format: 'svg', scale: 2 },
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  PlotlyChart                                                             ║
// ╚══════════════════════════════════════════════════════════════════════════╝

/**
 * Wrapper React per grafici Plotly provenienti dal backend.
 * Accetta direttamente il JSON di `fig.to_json()` e applica
 * i token del design system (colori, font) sovrascrivendo i valori hardcoded.
 *
 * Richiede `plotly.js-dist-min` installato:
 *   npm install plotly.js-dist-min
 *
 * @example
 * <PlotlyChart figure={result.univariate[col].charts.histogram} height={280} />
 */
export const PlotlyChart = memo(function PlotlyChart({
  figure,
  height    = 320,
  title,
  className = '',
}: PlotlyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const theme        = useUIStore(selectThemeResolved)
  const [error, setError]       = useState<string | null>(null)
  const [loading, setLoading]   = useState(true)

  // ── Render / re-render on figure or theme change ──────────────────────────
  const render = useCallback(async () => {
    const el = containerRef.current
    if (!el || !figure) return

    setLoading(true)
    setError(null)

    try {
      // Dynamic import: Plotly non va nel bundle critico
      const Plotly = (await import('plotly.js-dist-min' as string)) as typeof import('plotly.js')

      const overrides  = buildLayoutOverrides()
      const mergedLayout = deepMerge(
        figure.layout as Record<string, unknown>,
        overrides,
        { height, autosize: true },
      )

      await Plotly.react(
        el,
        figure.data as Data[],
        mergedLayout as Partial<Layout>,
        {
          ...PLOTLY_CONFIG,
          ...((figure.config ?? {}) as Record<string, unknown>),
        } as Partial<Config>,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore rendering grafico')
    } finally {
      setLoading(false)
    }
  }, [figure, theme, height]) // theme nel dep array: re-render al cambio dark/light

  useEffect(() => {
    render()
  }, [render])

  // ── Cleanup on unmount ────────────────────────────────────────────────────
  useEffect(() => {
    const el = containerRef.current
    return () => {
      if (!el) return
      import('plotly.js-dist-min' as string)
        .then((Plotly) => (Plotly as typeof import('plotly.js')).purge(el))
        .catch(() => undefined)
    }
  }, [])

  // ── Responsive resize ─────────────────────────────────────────────────────
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      import('plotly.js-dist-min' as string)
        .then((Plotly) => (Plotly as typeof import('plotly.js')).Plots.resize(el))
        .catch(() => undefined)
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // ── Empty state ───────────────────────────────────────────────────────────
  if (!figure) {
    return (
      <div
        className={`flex items-center justify-center rounded-[--radius-md] bg-[--color-surface-offset] border border-[--color-border] ${className}`}
        style={{ height }}
        aria-label="Nessun grafico disponibile"
      >
        <span className="text-[length:--text-sm] text-[--color-text-faint]">
          Nessun grafico
        </span>
      </div>
    )
  }

  // ── Error state ───────────────────────────────────────────────────────────
  if (error) {
    return (
      <div
        className={`flex flex-col items-center justify-center gap-2 rounded-[--radius-md] bg-[--color-error-highlight] border border-[--color-error-highlight] ${className}`}
        style={{ height }}
        role="alert"
      >
        <span className="text-[length:--text-sm] font-medium text-[--color-error]">
          Errore rendering
        </span>
        <span className="text-[length:--text-xs] text-[--color-error] opacity-70 max-w-xs text-center">
          {error}
        </span>
      </div>
    )
  }

  return (
    <div
      className={`relative ${className}`}
      style={{ height }}
      aria-label={title}
      role="img"
    >
      {/* Loading skeleton */}
      {loading && (
        <div
          className="absolute inset-0 rounded-[--radius-md] overflow-hidden"
          aria-hidden="true"
        >
          <div
            className="h-full w-full"
            style={{
              background: 'linear-gradient(90deg, var(--color-surface-offset) 25%, var(--color-surface-dynamic) 50%, var(--color-surface-offset) 75%)',
              backgroundSize: '200% 100%',
              animation: 'shimmer 1.5s ease-in-out infinite',
            }}
          />
        </div>
      )}
      {/* Plotly mount point */}
      <div ref={containerRef} className="w-full h-full" />
    </div>
  )
})

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Utility: deep merge (senza dipendenze esterne)                         ║
// ╚══════════════════════════════════════════════════════════════════════════╝

function deepMerge(
  ...sources: Record<string, unknown>[]
): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  for (const src of sources) {
    for (const [k, v] of Object.entries(src)) {
      if (
        v !== null &&
        typeof v === 'object' &&
        !Array.isArray(v) &&
        typeof result[k] === 'object' &&
        result[k] !== null &&
        !Array.isArray(result[k])
      ) {
        result[k] = deepMerge(
          result[k] as Record<string, unknown>,
          v as Record<string, unknown>,
        )
      } else {
        result[k] = v
      }
    }
  }
  return result
}
