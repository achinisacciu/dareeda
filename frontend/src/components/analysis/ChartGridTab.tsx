import { BarChart3 } from 'lucide-react'
import { PlotlyChart } from '@/components/ui/PlotlyChart'

export function ChartGridTab({ data, title = "Analisi" }: { data: unknown, title?: string }) {
  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-[--color-text-muted]">
        <BarChart3 className="w-12 h-12 mb-4 opacity-50" />
        <p>Nessun dato disponibile per {title.toLowerCase()}.</p>
      </div>
    )
  }

  function extractCharts(obj: unknown, depth = 0): { key: string; fig: unknown }[] {
    if (depth > 4 || !obj || typeof obj !== 'object') return []
    const result: { key: string; fig: unknown }[] = []
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      if (v && typeof v === 'object' && 'data' in v && 'layout' in v) {
        result.push({ key: k, fig: v })
      } else {
        result.push(...extractCharts(v, depth + 1))
      }
    }
    return result
  }

  const charts = extractCharts(data)
  if (charts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-[--color-text-muted]">
        <BarChart3 className="w-12 h-12 mb-4 opacity-50" />
        <p>Nessun grafico disponibile.</p>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-[1440px] mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1.5 h-8 bg-[--color-primary] rounded-full" />
        <h2 className="text-xl font-bold font-headline tracking-tight">{title}</h2>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        {charts.map(({ key, fig }) => (
          <div key={key} className="bg-[--color-surface-glass] border border-[--color-outline-variant] rounded-[--radius-card] shadow-sm overflow-hidden transition-all duration-180 hover:shadow-md">
            <div className="px-5 py-3 border-b border-[--color-outline-variant] bg-[--color-surface-offset]">
              <h3 className="font-headline font-bold text-xs uppercase tracking-wider text-[--color-text-muted]">
                {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </h3>
            </div>
            <div className="p-4">
              <PlotlyChart
                figure={fig as Parameters<typeof PlotlyChart>[0]['figure']}
                height={300}
                title={key}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}