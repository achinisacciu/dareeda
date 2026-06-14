import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { PlotlyChart } from '@/components/ui/PlotlyChart'
import { BarChart3 } from 'lucide-react'

export function ChartGridTab({ data, title = "Analisi" }: { data: unknown, title?: string }) {
  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-neutral-400">
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
      <div className="flex flex-col items-center justify-center p-12 text-neutral-400">
        <BarChart3 className="w-12 h-12 mb-4 opacity-50" />
        <p>Nessun grafico disponibile.</p>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-[1400px] mx-auto animate-fade-in">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-1.5 h-8 bg-[--color-primary] rounded-full"></div>
        <h2 className="text-2xl font-bold font-headline tracking-tight">{title}</h2>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {charts.map(({ key, fig }) => (
          <Card key={key}>
            <CardHeader title={key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} />
            <CardBody compact>
              <div className="p-4">
                <PlotlyChart
                  figure={fig as Parameters<typeof PlotlyChart>[0]['figure']}
                  height={300}
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
