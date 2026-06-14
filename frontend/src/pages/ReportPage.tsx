import { useState, useEffect, useRef } from 'react'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useUIStore } from '@/stores/uiStore'
import { reportsApi } from '@/api/analysis'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Card, CardHeader, CardBody } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { toast } from '@/stores/uiStore'
import type { AnalysisResult } from '@/types/analysis'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  ReportPage — Generazione e download del report PDF                     ║
// ║                                                                          ║
// ║  Il backend dareeda genera il PDF in modo sincrono:                     ║
// ║    POST /api/reports/generate-pdf  →  Blob PDF                          ║
// ║  Non esiste polling, status, né URL persistente.                        ║
// ╚══════════════════════════════════════════════════════════════════════════╝

import { FileText, Download, Zap, Loader2 } from 'lucide-react'

// ── Helper: costruisce analysis_data da AnalysisResult ────────────────────────

function buildAnalysisData(result: AnalysisResult): Record<string, unknown> {
  const data: Record<string, unknown> = {}
  if (result.overview)        data.overview        = result.overview
  if (result.data_quality)    data.data_quality    = result.data_quality
  if (result.univariate)      data.univariate      = result.univariate
  if (result.bivariate)       data.bivariate       = result.bivariate
  if (result.multivariate)    data.multivariate    = result.multivariate
  if (result.timeseries)      data.timeseries      = result.timeseries
  if (result.ml_exploratory)  data.ml_exploratory  = result.ml_exploratory
  if (result.enterprise)      data.enterprise      = result.enterprise
  if (result.insights)        data.insights        = result.insights
  if (result.meta)            data.meta            = result.meta
  if (result.feature_engineering) data.feature_engineering = result.feature_engineering
  return data
}

// ── ReportPreview ─────────────────────────────────────────────────────────────

function ReportPreview({ blobUrl }: { blobUrl: string }) {
  const [loaded, setLoaded] = useState(false)
  return (
    <Card variant="flat" className="overflow-hidden">
      <CardHeader title="Anteprima PDF" />
      <div className="relative border-t border-[--color-divider]" style={{ height: '70vh' }}>
        {!loaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-[--color-surface]">
            <span className="flex items-center gap-[--space-2] text-[length:--text-sm] text-[--color-text-muted]">
              <Loader2 className="animate-spin w-4 h-4" /> Caricamento anteprima…
            </span>
          </div>
        )}
        <iframe
          src={blobUrl}
          title="Anteprima report PDF"
          onLoad={() => setLoaded(true)}
          className="w-full h-full border-0"
        />
      </div>
    </Card>
  )
}

// ── ModuleSummary ─────────────────────────────────────────────────────────────

const MODULE_LABELS: Record<string, string> = {
  overview:       'Overview',
  data_quality:   'Data Quality',
  univariate:     'Analisi Univariata',
  bivariate:      'Analisi Bivariata',
  multivariate:   'Analisi Multivariata',
  timeseries:     'Serie Temporali',
  ml_exploratory: 'ML Esplorativo',
  insights:       'Insights',
  enterprise:     'Enterprise',
}

function ModuleSummary({ result }: { result: AnalysisResult }) {
  const modules = Object.entries(MODULE_LABELS).filter(([key]) =>
    result[key as keyof AnalysisResult] !== undefined,
  )
  if (modules.length === 0) return null
  return (
    <Card>
      <CardHeader title="Moduli inclusi nel report" />
      <CardBody>
        <div className="flex flex-wrap gap-[--space-2]">
          {modules.map(([key, label]) => (
            <Badge key={key} variant="success" size="sm" dot>
              {label}
            </Badge>
          ))}
        </div>
      </CardBody>
    </Card>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  ReportPage                                                              ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export default function ReportPage() {
  const currentProject = useAnalysisStore((s) => s.currentProject)
  const result         = useAnalysisStore((s) => s.result)
  const setActivePage  = useUIStore((s) => s.setActivePage)
  const openModal      = useUIStore((s) => s.openModal)

  const [isGenerating, setIsGenerating] = useState(false)
  const [blobUrl,      setBlobUrl]      = useState<string | null>(null)
  const [hasError,     setHasError]     = useState(false)
  const [errorMsg,     setErrorMsg]     = useState<string>('')

  // Cleanup blob URL on unmount o quando cambia progetto
  const prevBlobRef = useRef<string | null>(null)
  useEffect(() => {
    return () => {
      if (prevBlobRef.current) URL.revokeObjectURL(prevBlobRef.current)
    }
  }, [])

  // Azzera il report quando cambia progetto
  useEffect(() => {
    if (prevBlobRef.current) {
      URL.revokeObjectURL(prevBlobRef.current)
      prevBlobRef.current = null
    }
    setBlobUrl(null)
    setHasError(false)
    setErrorMsg('')
  }, [currentProject?.id])

  // ── Genera PDF ────────────────────────────────────────────────────────────

  async function handleGenerate() {
    if (!result || isGenerating) return
    setIsGenerating(true)
    setHasError(false)
    setErrorMsg('')

    // Revoca il vecchio blob URL prima di crearne uno nuovo
    if (prevBlobRef.current) {
      URL.revokeObjectURL(prevBlobRef.current)
      prevBlobRef.current = null
      setBlobUrl(null)
    }

    try {
      const analysisData = buildAnalysisData(result)
      const blob = await reportsApi.generatePdf(analysisData)
      const url  = URL.createObjectURL(blob)
      prevBlobRef.current = url
      setBlobUrl(url)
      toast.success('Report generato', 'Il PDF è pronto per il download.')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Errore sconosciuto'
      setHasError(true)
      setErrorMsg(msg)
      toast.error('Generazione fallita', msg)
    } finally {
      setIsGenerating(false)
    }
  }

  // ── Scarica PDF ───────────────────────────────────────────────────────────

  function handleDownload() {
    if (!blobUrl || !currentProject) return
    const a      = document.createElement('a')
    a.href       = blobUrl
    a.download   = `${currentProject.filename.replace(/\.[^.]+$/, '')}-report.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  // ── Guards ────────────────────────────────────────────────────────────────

  if (!currentProject) {
    return (
      <div className="h-full flex items-center justify-center">
        <EmptyState
          icon={<FileText className="w-12 h-12" />}
          title="Nessun progetto selezionato"
          description="Apri un progetto dalla pagina di upload per generare il report."
          action={{
            label:   "Vai all'upload",
            onClick: () => setActivePage('upload'),
            variant: 'primary',
          }}
        />
      </div>
    )
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center">
        <EmptyState
          icon={<FileText className="w-12 h-12" />}
          title="Analisi non completata"
          description="Esegui l'analisi EDA prima di generare il report."
          action={{
            label:   "Vai all'analisi",
            onClick: () => setActivePage('analysis'),
            variant: 'primary',
          }}
        />
      </div>
    )
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-[--content-wide] mx-auto px-[--space-6] py-[--space-8] flex flex-col gap-[--space-6]">

        {/* ── Header ────────────────────────────────────────────────────── */}
        <div>
          <div className="flex items-center gap-[--space-2] mb-[--space-1]">
            <h1 className="text-[length:--text-lg] font-bold text-[--color-text] leading-tight">
              Report
            </h1>
            <Badge variant="muted" size="sm">
              {currentProject.filename}
            </Badge>
          </div>
          <p className="text-[length:--text-sm] text-[--color-text-muted]">
            Genera il documento PDF riepilogativo dell&apos;analisi EDA.
          </p>
        </div>

        {/* ── Azioni ────────────────────────────────────────────────────── */}
        <Card>
          <CardBody>
            <div className="flex flex-wrap items-center justify-between gap-[--space-4]">
              <div className="flex items-center gap-[--space-3]">
                {blobUrl && !isGenerating && (
                  <Badge variant="success" size="sm" dot>PDF pronto</Badge>
                )}
                {isGenerating && (
                  <span className="flex items-center gap-[--space-1] text-[length:--text-xs] text-[--color-text-muted]">
                    <Loader2 className="animate-spin w-3 h-3" /> Generazione in corso…
                  </span>
                )}
                {!blobUrl && !isGenerating && !hasError && (
                  <span className="text-[length:--text-xs] text-[--color-text-faint]">
                    Nessun report generato
                  </span>
                )}
                {hasError && (
                  <Badge variant="error" size="sm" dot>Errore</Badge>
                )}
              </div>

              <div className="flex items-center gap-[--space-2]">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openModal('report_sections')}
                >
                  Sezioni
                </Button>

                {blobUrl && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownload}
                    icon={<Download className="w-4 h-4" />}
                  >
                    Scarica PDF
                  </Button>
                )}

                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  icon={isGenerating ? <Loader2 className="animate-spin w-4 h-4" /> : <Zap className="w-4 h-4" />}
                >
                  {blobUrl ? 'Rigenera' : 'Genera report'}
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* ── Errore ────────────────────────────────────────────────────── */}
        {hasError && errorMsg && (
          <div className="px-[--space-4] py-[--space-3] rounded-[--radius-lg] bg-[--color-error-highlight] text-[--color-error] text-[length:--text-sm]">
            {errorMsg}
          </div>
        )}

        {/* ── Moduli inclusi ────────────────────────────────────────────── */}
        <ModuleSummary result={result} />

        {/* ── Anteprima PDF ─────────────────────────────────────────────── */}
        {blobUrl && <ReportPreview blobUrl={blobUrl} />}

        {/* ── Placeholder ───────────────────────────────────────────────── */}
        {!blobUrl && !isGenerating && (
          <Card variant="flat">
            <div className="flex flex-col items-center justify-center py-[--space-16] gap-[--space-4]">
              <div className="text-[--color-text-faint]">
                <FileText className="w-16 h-16" />
              </div>
              <p className="text-[length:--text-sm] text-[--color-text-muted]">
                Clicca <strong>Genera report</strong> per creare il documento PDF.
              </p>
            </div>
          </Card>
        )}

      </div>
    </div>
  )
}
