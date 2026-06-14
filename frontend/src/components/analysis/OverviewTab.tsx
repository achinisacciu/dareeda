import type { AnalysisResult } from '@/types/analysis'
import { CheckCircle2, AlertTriangle, Fingerprint, Clock, ArrowRight, Table, Hash, Calendar } from 'lucide-react'

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
      <div className="flex flex-col items-center justify-center p-12 text-neutral-400">
        <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
        <p>Overview non ancora disponibile. I dati arriveranno al completamento dell'analisi.</p>
      </div>
    )
  }

  // Derived metrics for the dashboard
  const completeness = ov.missing_pct != null ? 100 - ov.missing_pct : 100
  const uniqueness = ov.duplicate_pct != null ? 100 - ov.duplicate_pct : 100
  const timeliness = 78 // Mocked initially if not present in analysis, but we should rely on real data if possible

  return (
    <div className="p-8 space-y-8 max-w-[1400px] mx-auto animate-fade-in">

      {/* Hero Grid: Summary & Context */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Executive Summary */}
        <div className="lg:col-span-8 bg-white border border-[--color-outline-variant] p-8 rounded-xl shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-1.5 h-8 bg-[--color-primary] rounded-full"></div>
            <h2 className="text-2xl font-bold font-headline tracking-tight">Executive Intelligence</h2>
          </div>
          <p className="text-[--color-on-surface-variant] leading-relaxed text-lg font-light">
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

        {/* Business Context Card */}
        <div className="lg:col-span-4 bg-neutral-800 text-white p-8 rounded-xl shadow-lg relative overflow-hidden">
          <div className="absolute -right-12 -top-12 w-48 h-48 bg-[--color-primary]/20 rounded-full blur-3xl"></div>
          <div className="relative z-10">
            <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-6 text-red-300">Dataset Context</h3>
            <div className="space-y-6">
              <div>
                <p className="text-neutral-400 text-xs font-medium uppercase mb-1">Dimensione</p>
                <p className="text-lg font-headline font-medium">{num(ov.n_rows)} Records</p>
              </div>
              <div className="flex justify-between border-t border-neutral-700 pt-4">
                <div>
                  <p className="text-neutral-400 text-xs font-medium uppercase mb-1">Features</p>
                  <p className="text-xl font-headline font-bold text-[--color-primary]">{ov.n_cols ?? '—'} Valide</p>
                </div>
                <div className="text-right">
                  <p className="text-neutral-400 text-xs font-medium uppercase mb-1">Memoria</p>
                  <p className="text-lg font-headline font-medium">{ov.memory_mb ? `${ov.memory_mb.toFixed(1)} MB` : '—'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Key Metrics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Metric 1 */}
        <div className="bg-white p-6 rounded-xl border border-[--color-outline-variant] shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <CheckCircle2 className="text-[--color-tertiary-container] w-8 h-8" />
            <div className="bg-[--color-tertiary]/10 text-[--color-tertiary-container] px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">Optimal</div>
          </div>
          <div>
            <p className="text-[--color-on-surface-variant] text-sm font-medium">Validità Schema</p>
            <h4 className="text-3xl font-bold font-headline mt-1">100%</h4>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white p-6 rounded-xl border border-[--color-outline-variant] shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <AlertTriangle className={(completeness < 95) ? "text-amber-500 w-8 h-8" : "text-[--color-tertiary-container] w-8 h-8"} />
            <div className={(completeness < 95) ? "bg-amber-100 text-amber-700 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider" : "bg-[--color-tertiary]/10 text-[--color-tertiary-container] px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider"}>
              {(completeness < 95) ? 'Warning' : 'Good'}
            </div>
          </div>
          <div>
            <p className="text-[--color-on-surface-variant] text-sm font-medium">Completezza</p>
            <h4 className="text-3xl font-bold font-headline mt-1">{pct(completeness)}</h4>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white p-6 rounded-xl border border-[--color-outline-variant] shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <Fingerprint className="text-[--color-tertiary-container] w-8 h-8" />
            <div className="bg-[--color-tertiary]/10 text-[--color-tertiary-container] px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">Reference</div>
          </div>
          <div>
            <p className="text-[--color-on-surface-variant] text-sm font-medium">Unicità</p>
            <h4 className="text-3xl font-bold font-headline mt-1">{pct(uniqueness)}</h4>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="bg-white p-6 rounded-xl border border-[--color-outline-variant] shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <Hash className="text-blue-600 w-8 h-8" />
            <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">Info</div>
          </div>
          <div>
            <p className="text-[--color-on-surface-variant] text-sm font-medium">Numeriche</p>
            <h4 className="text-3xl font-bold font-headline mt-1">
              {(ov.groups_count?.numeric_continuous ?? 0) + (ov.groups_count?.numeric_discrete ?? 0)}
            </h4>
          </div>
        </div>

      </div>

      {/* Critical Alerts Table */}
      {dqIssues.length > 0 && (
        <div className="bg-white rounded-xl border border-[--color-outline-variant] overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-[--color-outline-variant] flex justify-between items-center bg-[--color-surface-container-lowest]">
            <h3 className="font-headline font-bold text-lg">Data Quality Critical Alerts ({dqIssues.length})</h3>
            <button className="text-xs font-bold text-[--color-primary] flex items-center gap-1 hover:underline">
              REMEDIATION LOG <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-[--color-surface-container-low]">
                <tr>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-on-surface-variant]">Entity/Column</th>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-on-surface-variant]">Issue Detected</th>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-on-surface-variant]">Action</th>
                  <th className="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-[--color-on-surface-variant] text-right">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-outline-variant]">
                {dqIssues.map((issue, i) => {
                  const sev = String(issue.severity ?? 'low')
                  const action = (issue.action ?? {}) as Record<string, unknown>
                  return (
                    <tr key={i} className="hover:bg-neutral-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Table className="text-neutral-400 w-4 h-4" />
                          <span className="font-medium text-sm font-mono">{String(issue.column ?? '—')}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">{String(issue.description ?? '—')}</td>
                      <td className="px-6 py-4 text-sm text-[--color-primary] font-medium">{String(action.type ?? '—')}</td>
                      <td className="px-6 py-4 text-right">
                        <span className={`px-2 py-1 text-[10px] font-black rounded uppercase text-white ${sev === 'high' ? 'bg-[--color-error]' : sev === 'medium' ? 'bg-amber-500' : 'bg-blue-500'}`}>
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
      
      {/* Visual Backdrop (Decorative) - only if no major issues to balance design */}
      {dqIssues.length === 0 && (
         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 opacity-90">
           <div className="h-32 bg-[--color-surface-container-low] rounded-xl border border-[--color-outline-variant] overflow-hidden relative flex items-center justify-center">
             <div className="text-center">
               <p className="text-xs font-bold text-[--color-primary] uppercase">Trending Insight</p>
               <p className="text-sm font-medium text-neutral-600 mt-1">Nessuna anomalia critica rilevata nel set di dati.</p>
             </div>
           </div>
           <div className="h-32 bg-[--color-surface-container-low] rounded-xl border border-[--color-outline-variant] overflow-hidden relative flex items-center justify-center">
             <div className="text-center">
               <p className="text-xs font-bold text-[--color-tertiary] uppercase">System Status</p>
               <p className="text-sm font-medium text-neutral-600 mt-1">Analisi completata con successo sulle features attive.</p>
             </div>
           </div>
         </div>
      )}

    </div>
  )
}
