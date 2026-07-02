import type { AnalysisResult } from '@/types/analysis'
import { AlertTriangle, Table } from 'lucide-react'
import { KpiCards } from './KpiCards'

// Helpers
function pct(n: number | undefined | null): string {
  return `${(n ?? 0).toFixed(1)}%`
}

function num(n: number | undefined | null): string {
  return (n ?? 0).toLocaleString('it-IT')
}

export function OverviewTab({ result }: { result: AnalysisResult }) {
  const ov = result.overview
  const dq = result.data_quality as Record<string, unknown> | undefined
  const dqIssues = (dq?.standardized_issues ?? []) as Record<string, unknown>[]

  if (!ov) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-[--color-text-muted]">
        <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
        <p>Overview non ancora disponibile. I dati arriveranno al completamento dell'analisi.</p>
      </div>
    )
  }

  const uniqueness = ov.duplicate_pct != null ? 100 - ov.duplicate_pct : 100

  return (
    <div className="p-6 space-y-6 max-w-[1440px] mx-auto">

      {/* KPI strip */}
      <KpiCards />

      {/* Executive + Context */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 bg-[--color-surface-glass] border border-[--color-outline-variant] rounded-[--radius-card] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-1.5 h-8 bg-[--color-primary] rounded-full" />
            <h2 className="text-xl font-bold font-headline tracking-tight">Executive Intelligence</h2>
          </div>
          <p className="text-[--color-on-surface-variant] leading-relaxed">
            Il dataset analizzato presenta <strong>{num(ov.n_rows)}</strong> righe e <strong>{ov.n_cols ?? '—'}</strong> colonne.
            Il livello di unicità è al <strong>{pct(uniqueness)}</strong>.
            {(ov.missing_pct ?? 0) > 0 ? (
              <span> Sono presenti <span className="text-[--color-error] font-semibold">{pct(ov.missing_pct)}</span> di valori mancanti che richiedono attenzione.</span>
            ) : (
              <span> La completezza dei dati è ottimale.</span>
            )}
            {dqIssues.length > 0 && (
              <span> Sono state rilevate <span className="text-[--color-error] font-semibold">{dqIssues.length} anomalie critiche</span> di data quality.</span>
            )}
            L'utilizzo di memoria stimato è {ov.memory_human ?? (ov.memory_mb != null ? `${ov.memory_mb.toFixed(1)} MB` : 'Sconosciuto')}.
          </p>
        </div>

        <div className="lg:col-span-4 bg-[--color-surface] border border-[--color-outline-variant] rounded-[--radius-card] p-6 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-4 text-[--color-text-muted]">Dataset Context</h3>
          <div className="space-y-4">
            <div>
              <p className="text-[--color-text-faint] text-xs font-medium uppercase mb-1">Dimensione</p>
              <p className="text-lg font-headline font-medium">{num(ov.n_rows)} Records</p>
            </div>
            <div className="flex justify-between border-t border-[--color-divider] pt-4">
              <div>
                <p className="text-[--color-text-faint] text-xs font-medium uppercase mb-1">Features</p>
                <p className="text-xl font-headline font-bold text-[--color-primary]">{ov.n_cols ?? '—'} Valide</p>
              </div>
              <div className="text-right">
                <p className="text-[--color-text-faint] text-xs font-medium uppercase mb-1">Memoria</p>
                <p className="text-lg font-headline font-medium">{ov.memory_mb ? `${ov.memory_mb.toFixed(1)} MB` : '—'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {dqIssues.length > 0 && (
        <div className="bg-[--color-surface] rounded-[--radius-card] border border-[--color-outline-variant] shadow-sm">
          <div className="px-6 py-4 border-b border-[--color-outline-variant] flex justify-between items-center bg-[--color-surface-offset]">
            <h3 className="font-headline font-bold">Data Quality Critical Alerts ({dqIssues.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-[--color-surface-2]">
                <tr>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Entity/Column</th>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Issue Detected</th>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted]">Action</th>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-text-muted] text-right">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-divider]">
                {dqIssues.map((issue, i) => {
                  const sev = String(issue.severity ?? 'low')
                  const action = (issue.action ?? {}) as Record<string, unknown>
                  return (
                    <tr key={i} className="hover:bg-[--color-surface-2] transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Table className="text-[--color-text-faint] w-4 h-4" />
                          <span className="font-medium text-sm font-mono">{String(issue.column ?? '—')}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">{String(issue.description ?? '—')}</td>
                      <td className="px-6 py-4 text-sm text-[--color-primary] font-medium">{String(action.type ?? '—')}</td>
                      <td className="px-6 py-4 text-right">
                        <span className={`px-2 py-1 text-[10px] font-black rounded uppercase text-white ${sev === 'high' ? 'bg-[--color-error]' : sev === 'medium' ? 'bg-amber-500' : 'bg-[--color-info]'}`}>
                          {sev.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  )
}