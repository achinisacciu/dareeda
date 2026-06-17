import {
  useEffect, useRef, useCallback,
  type KeyboardEvent, type ReactElement, type ReactNode,
} from 'react'
import { createPortal } from 'react-dom'
import { useUIStore } from '@/stores/uiStore'
import { useAnalysisStore } from '@/stores/analysisStore'
import { toast } from '@/stores/uiStore'
import { Button } from '@/components/ui/Button'
import type { ModalId } from '@/stores/uiStore'
import type { ProblemType } from '@/types/analysis'
import { ANALYSIS_MODULE_ORDER } from '@/api/analysis'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  Base Modal shell                                                        ║
// ╚══════════════════════════════════════════════════════════════════════════╝

interface ModalShellProps {
  title:    string
  onClose:  () => void
  children: ReactNode
  /** Larghezza max del dialogo. Default: 480px */
  width?:   number | string
}

function ModalShell({ title, onClose, children, width = 480 }: ModalShellProps) {
  const dialogRef = useRef<HTMLDivElement>(null)

  // Focus trap
  useEffect(() => {
    const el = dialogRef.current
    if (!el) return
    const focusable = el.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    )
    focusable[0]?.focus()

    function handleTab(e: globalThis.KeyboardEvent) {
      if (e.key !== 'Tab' || !el) return
      const els = Array.from(
        el.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
        ),
      )
      if (els.length === 0) return
      const first = els[0], last = els[els.length - 1]
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus() }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', handleTab)
    return () => document.removeEventListener('keydown', handleTab)
  }, [])

  // ESC to close
  function handleKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Escape') onClose()
  }

  return createPortal(
    <div
      role="presentation"
      className="fixed inset-0 z-50 flex items-center justify-center p-[--space-4]"
      style={{ animation: 'fadeIn 180ms ease' }}
    >
      {/* Backdrop */}
      <div
        aria-hidden="true"
        onClick={onClose}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onKeyDown={handleKeyDown}
        className={[
          'relative flex flex-col',
          'rounded-[--radius-xl] border border-[--color-border]',
          'bg-[--color-surface-2] shadow-[--shadow-lg]',
          'max-h-[90dvh] overflow-hidden',
        ].join(' ')}
        style={{ width: '100%', maxWidth: width, animation: 'slideUp 220ms cubic-bezier(0.16,1,0.3,1)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-[--space-5] py-[--space-4] border-b border-[--color-divider] shrink-0">
          <h2 id="modal-title" className="text-[length:--text-sm] font-semibold text-[--color-text]">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Chiudi"
            className={[
              'flex items-center justify-center size-7 rounded-[--radius-sm]',
              'text-[--color-text-faint] hover:text-[--color-text] hover:bg-[--color-surface-offset]',
              'transition-[color,background] duration-[180ms]',
              'focus-visible:outline-2 focus-visible:outline-[--color-primary] focus-visible:outline-offset-1',
            ].join(' ')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-[--space-5] py-[--space-4]">
          {children}
        </div>
      </div>
    </div>,
    document.body,
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  delete_project                                                          ║
// ╚══════════════════════════════════════════════════════════════════════════╝

function DeleteProjectModal({ onClose }: { onClose: () => void }) {
  const payload        = useUIStore((s) => s.modal?.data as { projectId: string; filename: string } | null)
  const deleteProject  = useAnalysisStore((s) => s.deleteProject)
  const setActivePage  = useUIStore((s) => s.setActivePage)

  async function handleConfirm() {
    const projectId = payload?.projectId
    if (!projectId) return
    await deleteProject(projectId)
    setActivePage('upload')
    toast.success('Progetto eliminato')
    onClose()
  }

  return (
    <ModalShell title="Elimina progetto" onClose={onClose} width={420}>
      <div className="flex flex-col gap-[--space-4]">
        <p className="text-[length:--text-sm] text-[--color-text-muted] leading-relaxed">
          Stai per eliminare il progetto{' '}
          <strong className="text-[--color-text] font-semibold">
            {payload?.filename}
          </strong>
          {'.'}
          <br />
          Tutti i dati, i risultati e i report associati saranno rimossi definitivamente.
        </p>
        <div className="flex items-center justify-end gap-[--space-2] pt-[--space-2] border-t border-[--color-divider]">
          <Button variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
          <Button variant="danger" size="sm" onClick={handleConfirm}>Elimina</Button>
        </div>
      </div>
    </ModalShell>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  context_config                                                          ║
// ╚══════════════════════════════════════════════════════════════════════════╝

const PROBLEM_TYPES: { value: string; label: string }[] = [
  { value: '',               label: '— Non specificato —' },
  { value: 'classification', label: 'Classificazione' },
  { value: 'regression',     label: 'Regressione' },
]

function ContextConfigModal({ onClose }: { onClose: () => void }) {
  const currentProject  = useAnalysisStore((s) => s.currentProject)
  const updateContext   = useAnalysisStore((s) => s.updateContext)
  const result          = useAnalysisStore((s) => s.result)

  const columns: string[] = result
    ? Object.keys(result.univariate ?? {})
    : []

  const targetRef      = useRef<HTMLSelectElement>(null)
  const problemTypeRef = useRef<HTMLSelectElement>(null)

  async function handleSave() {
    await updateContext({
      target:       targetRef.current?.value || null,
      problem_type: (problemTypeRef.current?.value as ProblemType) || null,
    })
    toast.success('Contesto aggiornato')
    onClose()
  }

  return (
    <ModalShell title="Configura contesto analisi" onClose={onClose} width={440}>
      <div className="flex flex-col gap-[--space-4]">
        <p className="text-[length:--text-xs] text-[--color-text-muted] leading-relaxed">
          Specifica la colonna target e il tipo di problema per abilitare le analisi ML.
        </p>

        {/* Target column */}
        <div className="flex flex-col gap-[--space-1]">
          <label className="text-[length:--text-xs] font-semibold text-[--color-text-muted] uppercase tracking-wide">
            Colonna target
          </label>
          <select
            ref={targetRef}
            defaultValue={currentProject?.context?.target ?? ''}
            className={[
              'w-full rounded-[--radius-md] border border-[--color-border]',
              'bg-[--color-surface] text-[--color-text] text-[length:--text-sm]',
              'px-[--space-3] py-[--space-2]',
              'focus-visible:outline-2 focus-visible:outline-[--color-primary] focus-visible:outline-offset-1',
              'transition-[border-color] duration-[180ms]',
            ].join(' ')}
          >
            <option value="">— Nessuna —</option>
            {columns.map((col) => (
              <option key={col} value={col}>{col}</option>
            ))}
          </select>
        </div>

        {/* Problem type */}
        <div className="flex flex-col gap-[--space-1]">
          <label className="text-[length:--text-xs] font-semibold text-[--color-text-muted] uppercase tracking-wide">
            Tipo di problema
          </label>
          <select
            ref={problemTypeRef}
            defaultValue={currentProject?.context?.problem_type ?? ''}
            className={[
              'w-full rounded-[--radius-md] border border-[--color-border]',
              'bg-[--color-surface] text-[--color-text] text-[length:--text-sm]',
              'px-[--space-3] py-[--space-2]',
              'focus-visible:outline-2 focus-visible:outline-[--color-primary] focus-visible:outline-offset-1',
              'transition-[border-color] duration-[180ms]',
            ].join(' ')}
          >
            {PROBLEM_TYPES.map((pt) => (
              <option key={pt.value} value={pt.value}>{pt.label}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center justify-end gap-[--space-2] pt-[--space-2] border-t border-[--color-divider]">
          <Button variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
          <Button variant="primary" size="sm" onClick={handleSave}>Salva</Button>
        </div>
      </div>
    </ModalShell>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  run_confirm                                                             ║
// ╚══════════════════════════════════════════════════════════════════════════╝

function RunConfirmModal({ onClose }: { onClose: () => void }) {
  const runAnalysis   = useAnalysisStore((s) => s.runAnalysis)
  const setActivePage = useUIStore((s) => s.setActivePage)
  const hasResult     = useAnalysisStore((s) => s.result !== null)

  function handleConfirm() {
    runAnalysis()
    setActivePage('analysis')
    onClose()
  }

  return (
    <ModalShell title="Avvia analisi EDA" onClose={onClose} width={420}>
      <div className="flex flex-col gap-[--space-4]">
        {hasResult && (
          <div className="px-[--space-3] py-[--space-2] rounded-[--radius-md] bg-[--color-warning-highlight] text-[--color-warning] text-[length:--text-xs]">
            ⚠ È già presente un risultato. Avviare una nuova analisi lo sovrascriverà.
          </div>
        )}
        <p className="text-[length:--text-sm] text-[--color-text-muted] leading-relaxed">
          Verranno elaborati tutti i 9 moduli: overview, data quality, univariata, bivariata,
          multivariata, time series, ML exploratory, insights ed enterprise.
        </p>
        <div className="flex items-center justify-end gap-[--space-2] pt-[--space-2] border-t border-[--color-divider]">
          <Button variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
          <Button variant="primary" size="sm" onClick={handleConfirm}>Avvia</Button>
        </div>
      </div>
    </ModalShell>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  report_sections                                                         ║
// ╚══════════════════════════════════════════════════════════════════════════╝

const SECTION_LABELS: Record<string, string> = {
  overview:       'Overview',
  data_quality:   'Data Quality',
  univariate:     'Analisi Univariata',
  bivariate:      'Analisi Bivariata',
  multivariate:   'Analisi Multivariata',
  timeseries:     'Time Series',
  ml_exploratory: 'ML Exploratory',
  insights:       'Insights',
  enterprise:     'Enterprise Report',
}

function ReportSectionsModal({ onClose }: { onClose: () => void }) {
  const generateReport = useAnalysisStore((s) => s.result)
  const openModal      = useUIStore((s) => s.openModal)
  const selectedRef    = useRef<Set<string>>(new Set(ANALYSIS_MODULE_ORDER))

  function toggle(mod: string) {
    if (selectedRef.current.has(mod)) selectedRef.current.delete(mod)
    else selectedRef.current.add(mod)
  }

  function handleGenerate() {
    toast.info('Generazione report avviata…')
    onClose()
  }

  return (
    <ModalShell title="Sezioni da includere nel report" onClose={onClose} width={440}>
      <div className="flex flex-col gap-[--space-3]">
        {ANALYSIS_MODULE_ORDER.map((mod) => (
          <label
            key={mod}
            className={[
              'flex items-center gap-[--space-3] cursor-pointer',
              'px-[--space-3] py-[--space-2] rounded-[--radius-md]',
              'hover:bg-[--color-surface-offset] transition-[background] duration-[180ms]',
            ].join(' ')}
          >
            <input
              type="checkbox"
              defaultChecked
              onChange={() => toggle(mod)}
              className="size-4 accent-[--color-primary] cursor-pointer"
            />
            <span className="text-[length:--text-sm] text-[--color-text]">
              {SECTION_LABELS[mod]}
            </span>
          </label>
        ))}
        <div className="flex items-center justify-end gap-[--space-2] pt-[--space-2] border-t border-[--color-divider] mt-[--space-1]">
          <Button variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
          <Button variant="primary" size="sm" onClick={handleGenerate}>Genera report</Button>
        </div>
      </div>
    </ModalShell>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  ModalRenderer                                                           ║
// ╚══════════════════════════════════════════════════════════════════════════╝

const MODAL_MAP: Record<ModalId, (props: { onClose: () => void }) => ReactElement | null> = {
  delete_project:   DeleteProjectModal,
  context_config:   ContextConfigModal,
  run_confirm:      RunConfirmModal,
  cleaning_preview: ({ onClose }) => <ModalShell title="Anteprima pulizia" onClose={onClose}><p className="text-[length:--text-sm] text-[--color-text-muted]">Anteprima non disponibile.</p></ModalShell>,
  report_sections:  ReportSectionsModal,
}

/**
 * Renderizza il modal attivo in base a `uiStore.modal.id`.
 * Montare una sola volta in App.tsx:
 *   <ModalRenderer />
 */
export function ModalRenderer() {
  const modal      = useUIStore((s) => s.modal)
  const closeModal = useUIStore((s) => s.closeModal)

  if (!modal) return null

  const Content = MODAL_MAP[modal.id]
  if (!Content) return null

  return <Content onClose={closeModal} />
}
