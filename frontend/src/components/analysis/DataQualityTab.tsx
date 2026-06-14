import { useAnalysisStore } from '@/stores/analysisStore'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { PlotlyChart } from '@/components/ui/PlotlyChart'
import { Badge } from '@/components/ui/Badge'
import { StatCard } from '@/components/ui/StatCard'
import { AlertTriangle, Fingerprint, Activity, CheckCircle2 } from 'lucide-react'
import type { AnalysisResult } from '@/types/analysis'

function num(n: number | undefined | null): string {
  return (n ?? 0).toLocaleString('it-IT')
}

export function DataQualityTab({ result }: { result: AnalysisResult }) {
  const dq = result.data_quality
  if (!dq) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-neutral-400">
        <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
        <p>Data quality non disponibile.</p>
      </div>
    )
  }

  const dqAny      = dq as Record<string, unknown>
  const missing    = (dqAny.missing    ?? {}) as Record<string, unknown>
  const duplicates = (dqAny.duplicates ?? {}) as Record<string, unknown>
  const issues     = (dqAny.standardized_issues ?? []) as Record<string, unknown>[]

  return (
    <div className="p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1.5 h-8 bg-amber-500 rounded-full"></div>
        <h2 className="text-2xl font-bold font-headline tracking-tight">Data Quality Assessment</h2>
      </div>

      {/* Summary KPI */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Missing cells"
          value={num(missing.total_missing_cells as number)}
          icon={<AlertTriangle />}
          variant={'warning'}
        />
        <StatCard
          label="Duplicati"
          value={num(duplicates.n_duplicates as number)}
          icon={<Fingerprint />}
          variant="warning"
        />
        <StatCard
          label="Problemi totali"
          value={issues.length}
          icon={<Activity />}
          variant={issues.length > 0 ? 'error' : 'success'}
        />
        <StatCard
          label="Status"
          value={issues.length === 0 ? "Clean" : "Needs Review"}
          icon={<CheckCircle2 />}
        />
      </div>

      {/* Charts */}
      {!!dqAny.charts && (
        <div className="grid gap-6 lg:grid-cols-2">
          {Object.entries(dqAny.charts as Record<string, unknown>).map(([key, fig]) => (
            <Card key={key}>
              <CardHeader title={key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} />
              <CardBody compact>
                <div className="p-4">
                  <PlotlyChart
                    figure={fig as Parameters<typeof PlotlyChart>[0]['figure']}
                    height={320}
                    title={key}
                  />
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Issues table */}
      {issues.length > 0 && (
        <Card>
          <div className="px-6 py-4 border-b border-[--color-outline-variant] bg-[--color-surface-container-low]">
            <h3 className="font-headline font-bold text-lg">Problemi rilevati ({issues.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-[--color-surface-container-lowest]">
                <tr>
                  {['Colonna', 'Tipo', 'Severità', 'Descrizione', 'Azione'].map((h) => (
                    <th
                      key={h}
                      className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-on-surface-variant]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-outline-variant]">
                {issues.map((issue, i) => {
                  const sev        = String(issue.severity ?? 'low')
                  const action     = (issue.action ?? {}) as Record<string, unknown>
                  return (
                    <tr
                      key={i}
                      className="hover:bg-neutral-50 transition-colors"
                    >
                      <td className="px-6 py-4 font-mono text-sm font-medium">
                        {String(issue.column ?? '—')}
                      </td>
                      <td className="px-6 py-4 text-sm text-[--color-on-surface-variant]">
                        {String(issue.issue_type ?? '—')}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-[10px] font-black rounded uppercase text-white ${sev === 'high' ? 'bg-[--color-error]' : sev === 'medium' ? 'bg-amber-500' : 'bg-blue-500'}`}>
                          {sev.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-[--color-on-surface-variant] max-w-md truncate">
                        {String(issue.description ?? '—')}
                      </td>
                      <td className="px-6 py-4 text-sm text-[--color-primary] font-medium">
                        {String(action.type ?? '—')}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
