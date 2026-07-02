import { useAnalysisStore, selectOverallProgress, selectIsRunning } from '@/stores/analysisStore'
import { useUIStore, type AnalysisTab } from '@/stores/uiStore'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Play, Settings, FileText, XCircle, RefreshCw, Loader2 } from 'lucide-react'

// Import the separated Tabs
import { OverviewTab } from '@/components/analysis/OverviewTab'
import { DataQualityTab } from '@/components/analysis/DataQualityTab'
import { UnivariateTab } from '@/components/analysis/UnivariateTab'
import { ChartGridTab } from '@/components/analysis/ChartGridTab'


// ── Tab definitions ───────────────────────────────────────────────────────────

const TABS: { id: AnalysisTab; label: string }[] = [
  { id: 'overview',       label: 'Overview' },
  { id: 'data_quality',   label: 'Data Quality' },
  { id: 'univariate',     label: 'Univariata' },
  { id: 'bivariate',      label: 'Bivariata' },
  { id: 'multivariate',   label: 'Multivariata' },
  { id: 'timeseries',     label: 'Time Series' },
  { id: 'ml_exploratory', label: 'ML' },
  { id: 'enterprise',     label: 'Enterprise' },
  { id: 'insights',       label: 'Insights' },
]

// Helpers
function num(n: number | undefined | null): string {
  return (n ?? 0).toLocaleString('it-IT')
}

// ── Page header ───────────────────────────────────────────────────────────────

function AnalysisHeader() {
  const currentProject = useAnalysisStore((s) => s.currentProject)
  const analysisStatus = useAnalysisStore((s) => s.analysisStatus)
  const openModal      = useUIStore((s) => s.openModal)
  const isRunning      = useAnalysisStore(selectIsRunning)
  const cancelAnalysis = useAnalysisStore((s) => s.cancelAnalysis)
  const result         = useAnalysisStore((s) => s.result)

  return (
    <header className="shrink-0 px-6 py-4 border-b border-[--color-outline-variant] bg-white sticky top-0 z-10 flex items-center justify-between">
      {/* Left: filename + meta */}
      <div className="flex flex-col gap-1 min-w-0">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold font-headline text-[--color-on-surface] truncate tracking-tight">
            {currentProject?.filename ?? 'Dataset non caricato'}
          </h1>
          {analysisStatus === 'complete' ? <Badge variant="success" size="sm" dot>Completata</Badge> : null}
          {analysisStatus === 'error' ? <Badge variant="error" size="sm" dot>Errore</Badge> : null}
          {isRunning ? <Badge variant="info" size="sm" dot>In corso</Badge> : null}
        </div>

        {currentProject ? (
          <div className="flex items-center gap-2 text-xs font-medium text-[--color-on-surface-variant]">
            <span className="tabular-nums font-mono bg-neutral-100 px-1.5 py-0.5 rounded">{num(currentProject.n_rows)} righe</span>
            <span className="tabular-nums font-mono bg-neutral-100 px-1.5 py-0.5 rounded">{currentProject.n_cols ?? '—'} colonne</span>
          </div>
        ) : null}
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => openModal('context_config')}>
          <Settings className="w-4 h-4 mr-2" />
          Configura
        </Button>
        {result && (
          <Button variant="ghost" size="sm" onClick={() => openModal('report_sections')}>
            <FileText className="w-4 h-4 mr-2" />
            Report
          </Button>
        )}
        {isRunning ? (
          <Button variant="danger" size="sm" onClick={cancelAnalysis}>
            <XCircle className="w-4 h-4 mr-2" />
            Annulla
          </Button>
        ) : (
          <Button variant="primary" size="sm" onClick={() => openModal('run_confirm')}>
            {result ? <><RefreshCw className="w-4 h-4 mr-2" /> Riesegui</> : <><Play className="w-4 h-4 mr-2" /> Avvia Executive Run</>}
          </Button>
        )}
      </div>
    </header>
  )
}


// ── Progress bar ──────────────────────────────────────────────────────────────

function RunningProgressBar() {
  const isRunning       = useAnalysisStore(selectIsRunning)
  const overallProgress = useAnalysisStore(selectOverallProgress)
  const currentModule   = useAnalysisStore((s) => s.currentModule)
  const msg             = useAnalysisStore((s) => s.moduleMessages[currentModule ?? ''] ?? '')

  if (!isRunning) return null

  return (
    <div className="shrink-0 border-b border-[--color-outline-variant] bg-white">
      <div className="h-1 bg-[--color-surface-container-high] relative overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-[--color-primary] transition-all duration-300 ease-out"
          style={{ width: `${overallProgress}%` }}
        />
      </div>

      <div className="px-6 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-3 text-[--color-on-surface-variant]">
          <Loader2 className="w-4 h-4 text-[--color-primary] animate-spin" />
          <span className="font-bold text-[--color-on-surface] uppercase tracking-widest">
            {currentModule ? currentModule.replace(/_/g, ' ') : 'Analisi in corso'}
          </span>
          {msg ? <span className="text-neutral-500 font-medium truncate max-w-sm ml-2">— {msg}</span> : null}
        </div>
        <span className="font-headline font-bold text-sm text-[--color-primary]">
          {overallProgress}%
        </span>
      </div>
    </div>
  )
}


// ── Tab bar — segmented control ───────────────────────────────────────────────

function TabBar() {
  const activeTab    = useUIStore((s) => s.activeTab)
  const setActiveTab = useUIStore((s) => s.setActiveTab)

  return (
    <div className="shrink-0 border-b border-[--color-outline-variant] bg-white px-2 pt-2">
      <div className="overflow-x-auto custom-scrollbar flex gap-1">
        {TABS.map((tab) => {
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={active}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-4 py-2.5 text-xs font-bold font-headline uppercase tracking-widest transition-colors whitespace-nowrap
                border-b-2
                ${active
                  ? 'border-[--color-primary] text-[--color-primary] bg-[--color-primary]/5'
                  : 'border-transparent text-neutral-400 hover:text-neutral-700 hover:bg-neutral-50'
                }
              `}
            >
              {tab.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}


// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  AnalysisPage                                                            ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export default function AnalysisPage() {
  const result    = useAnalysisStore((s) => s.result)
  const status    = useAnalysisStore((s) => s.analysisStatus)
  const activeTab = useUIStore((s) => s.activeTab)

  return (
    <div className="h-full flex flex-col overflow-hidden bg-[--color-surface-container-lowest]">
      <AnalysisHeader />
      <RunningProgressBar />
      <TabBar />

      <div className={['flex-1 relative', activeTab === 'univariate' ? 'overflow-hidden' : 'overflow-y-auto custom-scrollbar'].join(' ')}>
        {!result && status !== 'running' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-8 bg-[--color-surface-container-lowest]">
            <Play className="w-16 h-16 text-[--color-primary] opacity-20 mb-6" />
            <h2 className="text-2xl font-bold font-headline mb-2 text-[--color-on-surface]">Pronto per l'analisi</h2>
            <p className="text-[--color-on-surface-variant] text-lg font-light max-w-md text-center">
              Clicca su "Avvia Executive Run" in alto a destra per processare il dataset e generare l'intelligence report.
            </p>
          </div>
        )}

        {result && (
          <div className="h-full pb-8">
            {activeTab === 'overview' ? <OverviewTab result={result} /> : null}
            {activeTab === 'data_quality' ? <DataQualityTab result={result} /> : null}
            {activeTab === 'univariate' ? <UnivariateTab result={result} /> : null}
            {activeTab === 'bivariate' ? <ChartGridTab data={result.bivariate} title="Analisi Bivariata" /> : null}
            {activeTab === 'multivariate' ? <ChartGridTab data={result.multivariate} title="Analisi Multivariata" /> : null}
            {activeTab === 'timeseries' ? <ChartGridTab data={result.timeseries} title="Time Series" /> : null}
            {activeTab === 'ml_exploratory' ? <ChartGridTab data={result.ml_exploratory} title="ML Exploratory" /> : null}
            {activeTab === 'enterprise' ? <ChartGridTab data={result.enterprise} title="Enterprise Patterns" /> : null}
            {activeTab === 'insights' ? (
               <div className="p-12 text-center text-neutral-400">
                 <p className="text-xl">Sezione Insights da completare secondo specifiche business.</p>
               </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
