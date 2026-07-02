import React from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  TrendingDown,
  Table,
  Activity,
  Image as ImageIcon,
  Sparkles,
  ArrowRight,
} from 'lucide-react'
import { PlotlyChart, type PlotlyFigure } from '@/components/ui/PlotlyChart'
import type { AnalysisResult } from '@/types/analysis'

function pct(n: number | undefined | null): string {
  return `${(n ?? 0).toFixed(1)}%`
}

function num(n: number | undefined | null): string {
  return (n ?? 0).toLocaleString('it-IT')
}

function severityIcon(sev: string) {
  switch (sev) {
    case 'high':
      return <XCircle className="w-4 h-4 text-[--color-error]" />
    case 'medium':
      return <AlertTriangle className="w-4 h-4 text-[--color-warning]" />
    default:
      return <CheckCircle2 className="w-4 h-4 text-[--color-info]" />
  }
}

function severityBadge(sev: string) {
  const cls =
    sev === 'high'
      ? 'bg-[--color-error-light] text-[--color-error] border-[--color-error]/30'
      : sev === 'medium'
        ? 'bg-[--color-warning-light] text-[--color-warning] border-[--color-warning]/30'
        : 'bg-[--color-info-light] text-[--color-info] border-[--color-info]/30'
  return (
    <span className={`px-2 py-1 text-[10px] font-black rounded border uppercase tracking-wider ${cls}`}>
      {sev.toUpperCase()}
    </span>
  )
}

export function DataQualityTab({ result }: { result: AnalysisResult }) {
  const dq = result.data_quality as Record<string, unknown> | undefined

  if (!dq) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-[--color-text-muted]">
        <Activity className="w-12 h-12 mb-4 opacity-50" />
        <p>Data Quality non ancora disponibile.</p>
      </div>
    )
  }

  const missing = (dq.missing ?? {}) as Record<string, unknown>
  const duplicates = (dq.duplicates ?? {}) as Record<string, unknown>
  const outliers = (dq.outliers ?? {}) as Record<string, unknown>
  const standardizedIssues = (dq.standardized_issues ?? []) as Record<string, unknown>[]
  const charts = (dq.charts ?? {}) as Record<string, unknown>
  const cleaningSummary = (dq.cleaning_summary ?? {}) as Record<string, unknown>

  const totalMissingCells = Number(missing.total_missing_cells ?? 0)
  const missingByColumn = (missing.missing_by_column ?? {}) as Record<string, number>
  const nDuplicateRows = Number(duplicates.n_duplicate_rows ?? duplicates.n_duplicates ?? 0)
  const pctDuplicateRows = Number(duplicates.pct_duplicate_rows ?? duplicates.duplicate_ratio ?? 0)
  const nOutliers = Number(outliers.n_outliers ?? 0)
  const outlierRatio = Number(outliers.outlier_ratio ?? 0)
  const outliersByColumn = (outliers.by_column ?? {}) as Record<string, number>

  const highIssues = standardizedIssues.filter((i) => String(i.severity) === 'high').length
  const medIssues = standardizedIssues.filter((i) => String(i.severity) === 'medium').length
  const lowIssues = standardizedIssues.filter((i) => String(i.severity) === 'low').length

  const heatmap = missing.missing_heatmap as { data?: unknown[]; layout?: Record<string, unknown> } | undefined
  const hasHeatmap = heatmap && Array.isArray(heatmap.data) && heatmap.data.length > 0

  return (
    <div className="p-6 space-y-8 max-w-[1440px] mx-auto">
      {/* ── KPI STRIP ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Celle mancanti"
          value={num(totalMissingCells)}
          icon={<TrendingDown className="w-5 h-5 text-[--color-warning]" />}
          variant="warning"
          subtitle={pct(0)} // placeholder; il vero pct richiede n_rows
        />
        <MetricCard
          label="Righe duplicate"
          value={num(nDuplicateRows)}
          icon={<Table className="w-5 h-5 text-[--color-info]" />}
          variant="info"
          subtitle={pct(pctDuplicateRows)}
        />
        <MetricCard
          label="Outliers"
          value={num(nOutliers)}
          icon={<Activity className="w-5 h-5 text-[--color-purple]" />}
          variant="purple"
          subtitle={pct(outlierRatio)}
        />
        <MetricCard
          label="Issue critiche"
          value={String(standardizedIssues.length)}
          icon={<AlertTriangle className="w-5 h-5 text-[--color-error]" />}
          variant="error"
          subtitle={`${highIssues} high · ${medIssues} med · ${lowIssues} low`}
        />
      </div>

      {/* ── CHARTS + MISSING HEATMAP ─────────────────────────── */}
      {(Object.keys(charts).length > 0 || hasHeatmap) && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-8 bg-[--color-primary] rounded-full" />
            <h2 className="text-xl font-bold font-headline tracking-tight">Visualizzazioni</h2>
          </div>
          <div className="grid gap-5 lg:grid-cols-2">
            {hasHeatmap && (
              <div className="bg-[--color-surface-glass] border border-[--color-outline-variant] rounded-[--radius-card] shadow-sm overflow-hidden">
                <div className="px-5 py-3 border-b border-[--color-outline-variant] bg-[--color-surface-offset] flex items-center gap-2">
                  <ImageIcon className="w-4 h-4 text-[--color-text-muted]" />
                  <h3 className="font-headline font-bold text-xs uppercase tracking-wider text-[--color-text-muted]">
                    Missing Values Heatmap
                  </h3>
                </div>
                <div className="p-4">
                <PlotlyChart
                    figure={{ data: heatmap.data as PlotlyFigure['data'], layout: heatmap.layout! }}
                    height={360}
                    title="missing_heatmap"
                  />
                </div>
              </div>
            )}
            {Object.entries(charts).map(([key, fig]) => (
              <div key={key} className="bg-[--color-surface-glass] border border-[--color-outline-variant] rounded-[--radius-card] shadow-sm overflow-hidden transition-all duration-180 hover:shadow-md">
                <div className="px-5 py-3 border-b border-[--color-outline-variant] bg-[--color-surface-offset]">
                  <h3 className="font-headline font-bold text-xs uppercase tracking-wider text-[--color-text-muted]">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </h3>
                </div>
                <div className="p-4">
                  <PlotlyChart
                    figure={fig as Parameters<typeof PlotlyChart>[0]['figure']}
                    height={320}
                    title={key}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── MISSING BY COLUMN ───────────────────────────────── */}
      {Object.keys(missingByColumn).length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-8 bg-[--color-primary] rounded-full" />
            <h2 className="text-xl font-bold font-headline tracking-tight">Completitudine per colonna</h2>
          </div>
          <div className="bg-[--color-surface] rounded-[--radius-card] border border-[--color-outline-variant] shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[--color-surface-offset]">
                  <tr>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Colonna</th>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted] text-right">Valori mancanti</th>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted] text-right">Completitudine</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[--color-divider]">
                  {Object.entries(missingByColumn)
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([col, count]) => {
                      const n = Number(count)
                      return (
                        <tr key={col} className="hover:bg-[--color-surface-2] transition-colors">
                          <td className="px-5 py-3">
                            <span className="font-medium text-sm font-mono">{col}</span>
                          </td>
                          <td className="px-5 py-3 text-sm text-right tabular-nums">{num(n)}</td>
                          <td className="px-5 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-24 h-1.5 rounded-full bg-[--color-surface-offset] overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-[--color-primary]"
                                  style={{
                                    width: `${Math.max(0, Math.min(100, 100 - (n / Math.max(1, totalMissingCells)) * 100))}%`,
                                  }}
                                />
                              </div>
                              <span className="text-xs font-bold text-[--color-text-muted] w-10 text-right">
                                {pct(100 - (n / Math.max(1, totalMissingCells)) * 100)}
                              </span>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* ── OUTLIERS BY COLUMN ───────────────────────────────── */}
      {Object.keys(outliersByColumn).length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-8 bg-[--color-primary] rounded-full" />
            <h2 className="text-xl font-bold font-headline tracking-tight">Outlier per colonna</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(outliersByColumn)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([col, count]) => (
                <div
                  key={col}
                  className="bg-[--color-surface-glass] border border-[--color-outline-variant] rounded-[--radius-card] p-4 shadow-sm transition-all duration-180 hover:shadow-md"
                >
                  <p className="text-[10px] font-bold text-[--color-text-muted] uppercase tracking-widest mb-1">
                    {col}
                  </p>
                  <p className="text-xl font-headline font-bold text-[--color-on-surface] tabular-nums">
                    {num(Number(count))}
                  </p>
                </div>
              ))}
          </div>
        </section>
      )}

      {/* ── STANDARDIZED ISSUES ─────────────────────────────── */}
      {standardizedIssues.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-8 bg-[--color-primary] rounded-full" />
            <h2 className="text-xl font-bold font-headline tracking-tight">Anomalie rilevate</h2>
            <span className="text-xs font-bold text-[--color-text-muted] bg-[--color-surface-offset] px-2 py-1 rounded-full">
              {standardizedIssues.length}
            </span>
          </div>
          <div className="bg-[--color-surface] rounded-[--color-outline-variant] border border-[--color-outline-variant] shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[--color-surface-offset]">
                  <tr>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Colonna</th>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Anomalia</th>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Dettagli</th>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Azione consigliata</th>
                    <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted] text-right">Severity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[--color-divider]">
                  {standardizedIssues.map((issue, i) => {
                    const sev = String(issue.severity ?? 'low')
                    const action = (issue.action ?? {}) as Record<string, unknown>
                    return (
                      <tr key={i} className="hover:bg-[--color-surface-2] transition-colors">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            <Table className="text-[--color-text-faint] w-4 h-4" />
                            <span className="font-medium text-sm font-mono">{String(issue.column ?? '—')}</span>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            {severityIcon(sev)}
                            <span className="text-sm font-medium">{String(issue.issue_type ?? '—')}</span>
                          </div>
                        </td>
                        <td className="px-5 py-4 text-sm text-[--color-text-muted] max-w-xs">
                          {issue.detection && typeof issue.detection === 'object' && 'summary' in issue.detection
                            ? String((issue.detection as Record<string, unknown>).summary)
                            : String(issue.description ?? '—')}
                        </td>
                        <td className="px-5 py-4 text-sm">
                          {action.type ? (
                            <span className="inline-flex items-center gap-1 text-[--color-primary] font-medium">
                              {String(action.type)} <ArrowRight className="w-3 h-3" />
                            </span>
                          ) : (
                            <span className="text-[--color-text-muted]">—</span>
                          )}
                        </td>
                        <td className="px-5 py-4 text-right">{severityBadge(sev)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* ── CLEANING SUMMARY ────────────────────────────────── */}
      {cleaningSummary && Object.keys(cleaningSummary).length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-8 bg-[--color-success] rounded-full" />
            <h2 className="text-xl font-bold font-headline tracking-tight">Riepilogo pulizia</h2>
            <Sparkles className="w-5 h-5 text-[--color-success]" />
          </div>
          <div className="bg-[--color-surface-glass] border border-[--color-outline-variant] rounded-[--radius-card] p-6 shadow-sm">
            <pre className="text-xs text-[--color-text-muted] whitespace-pre-wrap font-mono leading-relaxed">
              {JSON.stringify(cleaningSummary, null, 2)}
            </pre>
          </div>
        </section>
      )}
    </div>
  )
}

function MetricCard({
  label,
  value,
  icon,
  variant = 'info',
  subtitle,
}: {
  label: string
  value: string
  icon: React.ReactNode
  variant?: 'success' | 'warning' | 'info' | 'error' | 'purple'
  subtitle?: string
}) {
  const ring =
    variant === 'success'
      ? 'ring-[--color-success]/30'
      : variant === 'warning'
        ? 'ring-[--color-warning]/30'
        : variant === 'error'
          ? 'ring-[--color-error]/30'
          : variant === 'purple'
            ? 'ring-[--color-purple]/30'
            : 'ring-[--color-info]/30'

  return (
    <div
      className={`
        bg-[--color-surface-glass] border border-[--color-outline-variant] rounded-[--radius-card] p-5 shadow-sm
        flex flex-col justify-between transition-all duration-180 hover:shadow-md hover:-translate-y-0.5
        ring-1 ${ring}
      `}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2 text-[--color-text-muted]">{icon}</div>
        {subtitle ? <span className="text-[10px] font-bold text-[--color-text-faint] uppercase tracking-wider">{subtitle}</span> : null}
      </div>
      <div>
        <p className="text-[--color-text-muted] text-xs font-medium uppercase tracking-wide">{label}</p>
        <h4 className="text-3xl font-bold font-headline mt-1 leading-none tabular-nums">{value}</h4>
      </div>
    </div>
  )
}