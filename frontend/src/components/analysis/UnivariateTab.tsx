import { useUIStore } from '@/stores/uiStore'
import { SemanticTypeBadge } from '@/components/ui/Badge'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { PlotlyChart } from '@/components/ui/PlotlyChart'
import { AlertTriangle, ListFilter } from 'lucide-react'
import type { AnalysisResult } from '@/types/analysis'

function UnivariateDetail({
  columnResult,
  columnName: _columnName,
}: {
  columnResult: Record<string, unknown>
  columnName: string
}) {
  const charts  = (columnResult.charts  ?? {}) as Record<string, unknown>
  const stats   = (columnResult.stats   ?? {}) as Record<string, unknown>
  const comment = columnResult.ai_comment as string | undefined

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {comment && (
        <div className="px-6 py-4 rounded-xl border border-[--color-primary]/20 bg-[--color-primary]/5 text-[--color-primary] text-sm leading-relaxed shadow-sm">
          <strong>AI Insight:</strong> {comment}
        </div>
      )}

      {/* Stats grid */}
      {Object.keys(stats).length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Object.entries(stats).slice(0, 8).map(([k, v]) => (
            <div
              key={k}
              className="rounded-xl border border-[--color-outline-variant] bg-white p-4 shadow-sm"
            >
              <p className="text-[10px] font-bold text-[--color-on-surface-variant] uppercase tracking-widest mb-1">
                {k.replace(/_/g, ' ')}
              </p>
              <p className="text-xl font-headline font-bold text-[--color-on-surface] tabular-nums mt-px">
                {String(v ?? '—')}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {Object.entries(charts).map(([key, fig]) => (
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
    </div>
  )
}

export function UnivariateTab({ result }: { result: AnalysisResult }) {
  const activeColumn    = useUIStore((s) => s.activeColumn)
  const setActiveColumn = useUIStore((s) => s.setActiveColumn)
  const univ            = result.univariate ?? {}
  const columns         = Object.keys(univ)
  const selected        = activeColumn && univ[activeColumn] ? univ[activeColumn] : null

  return (
    <div className="flex h-[calc(100vh-140px)] overflow-hidden gap-0 bg-[--color-surface-container-lowest]">
      {/* Column list Sidebar */}
      <aside className="w-72 shrink-0 border-r border-[--color-outline-variant] bg-white flex flex-col h-full shadow-sm z-10">
        <div className="px-6 py-4 border-b border-[--color-outline-variant] bg-[--color-surface-container-low]">
          <div className="flex items-center gap-2 text-neutral-500 mb-1">
            <ListFilter className="w-4 h-4" />
            <span className="text-[10px] font-bold uppercase tracking-widest">Features</span>
          </div>
          <h3 className="font-headline font-bold text-lg">{columns.length} Colonne</h3>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {columns.length === 0 ? (
            <p className="px-6 py-4 text-sm text-[--color-on-surface-variant]">
              Nessuna colonna disponibile
            </p>
          ) : (
            <div className="p-2 space-y-1">
              {columns.map((col) => {
                const r     = univ[col]
                const stype = typeof r === 'object' && r !== null && 'semantic_type' in r
                  ? String((r as { semantic_type: unknown }).semantic_type)
                  : 'unknown'
                const isActive = activeColumn === col

                return (
                  <button
                    key={col}
                    type="button"
                    onClick={() => setActiveColumn(col)}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-lg text-left transition-colors cursor-pointer
                      ${isActive
                        ? 'bg-[--color-primary]/10 text-[--color-primary] font-bold'
                        : 'hover:bg-neutral-50 text-[--color-on-surface-variant]'
                      }
                    `}
                  >
                    <span className="text-sm font-medium font-mono truncate mr-2">
                      {col}
                    </span>
                    <SemanticTypeBadge type={stype} size="sm" />
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </aside>

      {/* Detail panel */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
        {!selected ? (
          <div className="flex flex-col items-center justify-center h-full text-neutral-400">
            <ListFilter className="w-12 h-12 mb-4 opacity-50" />
            <h3 className="font-headline font-bold text-xl text-[--color-on-surface] mb-2">Seleziona una colonna</h3>
            <p>Scegli una feature dalla lista per visualizzarne le distribuzioni.</p>
          </div>
        ) : (
          <div className="max-w-[1200px] mx-auto">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-1.5 h-8 bg-[--color-primary] rounded-full"></div>
              <div>
                <h2 className="text-2xl font-bold font-headline tracking-tight">{activeColumn}</h2>
                <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mt-1">Univariate Analysis</p>
              </div>
            </div>
            <UnivariateDetail
              columnResult={selected as Record<string, unknown>}
              columnName={activeColumn!}
            />
          </div>
        )}
      </div>
    </div>
  )
}
