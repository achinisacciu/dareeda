import { useUIStore, toast } from '@/stores/uiStore'
import {
  useAnalysisStore,
  selectOverallProgress,
  selectIsRunning,
} from '@/stores/analysisStore'
import { ANALYSIS_MODULE_ORDER } from '@/api/analysis'
import { FileText, BarChart3, Upload, Settings, HelpCircle, Grid3x3 } from 'lucide-react'
import { type ReactNode } from 'react'

const MODULE_LABELS: Record<string, string> = {
  overview: 'Overview',
  data_quality: 'Data quality',
  univariate: 'Univariata',
  bivariate: 'Bivariata',
  multivariate: 'Multivariata',
  timeseries: 'Time series',
  ml_exploratory: 'ML exploratory',
  insights: 'Insights',
  enterprise: 'Enterprise',
}

interface NavItemProps {
  icon: ReactNode
  label: string
  active: boolean
  disabled?: boolean
  onClick: () => void
}

function NavItem({ icon, label, active, disabled = false, onClick }: NavItemProps) {
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      className={`
        flex items-center w-full text-left gap-3 px-4 py-2.5 font-headline text-xs uppercase tracking-wider transition-colors duration-180
        ${active
          ? 'bg-[--color-surface-2] text-[--color-primary] border-r-4 border-[--color-primary] font-bold'
          : disabled
            ? 'text-[--color-text-faint] cursor-not-allowed'
            : 'text-[--color-text-muted] hover:text-[--color-text] hover:bg-[--color-surface-offset]'
        }
      `}
    >
      <span className="shrink-0 w-4 h-4 flex items-center justify-center">{icon}</span>
      <span className="truncate">{label}</span>
      {active ? <span className="ml-auto text-[8px] bg-[--color-primary]/10 text-[--color-primary] px-1.5 py-0.5 rounded font-bold">ACTIVE</span> : null}
    </button>
  )
}

function AnalysisProgress() {
  const status = useAnalysisStore((s) => s.analysisStatus)
  const completedMods = useAnalysisStore((s) => s.completedModules)
  const currentModule = useAnalysisStore((s) => s.currentModule)
  const currentPct = useAnalysisStore((s) => s.currentModulePct)
  const overallProgress = useAnalysisStore(selectOverallProgress)
  const isRunning = useAnalysisStore(selectIsRunning)

  if (status === 'idle') return null

  return (
    <div className="px-4 py-3 border-t border-[--color-divider]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] uppercase font-bold text-[--color-text-muted] tracking-wider">
          Analisi Status
        </span>
        <span className="text-[10px] font-bold text-[--color-primary] tabular-nums">
          {overallProgress}%
        </span>
      </div>

      <div className="h-1.5 rounded-full bg-[--color-surface-offset] overflow-hidden mb-3">
        <div
          className="h-full rounded-full bg-[--color-primary] transition-all duration-300 ease-out"
          style={{ width: `${overallProgress}%` }}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        {ANALYSIS_MODULE_ORDER.map((mod) => {
          const done = completedMods.includes(mod)
          const running = isRunning && currentModule === mod
          const pct = running ? currentPct : done ? 100 : 0

          return (
            <div key={mod} className="flex justify-between items-center text-[10px] font-headline tracking-wider">
              <span className={`truncate ${done ? 'text-[--color-text-muted]' : running ? 'text-[--color-text] font-bold' : 'text-[--color-text-faint]'}`}>
                {MODULE_LABELS[mod] ?? mod}
              </span>
              {(running || done) && (
                <span className={done ? 'text-[--color-success]' : 'text-[--color-primary]'}>
                  {done ? 'DONE' : `${pct}%`}
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function Sidebar() {
  const activePage = useUIStore((s) => s.activePage)
  const setActivePage = useUIStore((s) => s.setActivePage)

  const currentProject = useAnalysisStore((s) => s.currentProject)
  const hasResult = useAnalysisStore((s) => s.result !== null)
  const analysisStatus = useAnalysisStore((s) => s.analysisStatus)

  const canAnalyse = currentProject !== null
  const canReport = hasResult

  return (
    <aside className="fixed left-0 top-0 h-full flex flex-col bg-[--color-bg] w-64 border-r border-[--color-divider] shadow-lg z-50 overflow-hidden">
      {/* Brand Header */}
      <div className="p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 bg-[--color-primary] flex items-center justify-center rounded-[--radius-md] shadow-sm">
            <Grid3x3 className="text-white w-5 h-5" />
          </div>
          <h1 className="text-xl font-bold text-[--color-text] tracking-tight font-headline">Quantedge Matrix</h1>
        </div>
        <p className="font-headline text-[10px] tracking-[0.1em] text-[--color-text-muted] uppercase">
          v2.4 Enterprise — dareeda
        </p>
      </div>

      {/* Primary Navigation */}
      <nav className="flex-1 mt-2 overflow-y-auto custom-scrollbar">
        <div className="mb-4">
          <p className="px-4 text-[10px] font-bold text-[--color-text-faint] uppercase tracking-widest mb-2">Main Menu</p>
          <NavItem
            icon={<Upload className="w-4 h-4" />}
            label="Carica Dataset"
            active={activePage === 'upload'}
            onClick={() => setActivePage('upload')}
          />
          <NavItem
            icon={<BarChart3 className="w-4 h-4" />}
            label="Executive Intelligence"
            active={activePage === 'analysis'}
            disabled={!canAnalyse}
            onClick={() => {
              if (!canAnalyse) {
                toast.warning('Nessun progetto caricato', 'Carica prima un dataset.')
                return
              }
              setActivePage('analysis')
            }}
          />
          <NavItem
            icon={<FileText className="w-4 h-4" />}
            label="Report & Export"
            active={activePage === 'report'}
            disabled={!canReport}
            onClick={() => {
              if (!canReport) {
                toast.warning('Nessun risultato disponibile', "Esegui prima un'analisi.")
                return
              }
              setActivePage('report')
            }}
          />
        </div>

        {analysisStatus !== 'idle' ? <AnalysisProgress /> : null}
      </nav>

      {/* Footer Navigation */}
      <div className="mt-auto border-t border-[--color-divider] py-4">
        <button className="w-full flex items-center gap-3 px-4 py-2.5 text-[--color-text-muted] hover:text-[--color-text] transition-colors font-headline text-xs uppercase tracking-wider">
          <Settings className="w-4 h-4" /> Settings
        </button>
        <button className="w-full flex items-center gap-3 px-4 py-2.5 text-[--color-text-muted] hover:text-[--color-text] transition-colors font-headline text-xs uppercase tracking-wider">
          <HelpCircle className="w-4 h-4" /> Support
        </button>
      </div>
    </aside>
  )
}