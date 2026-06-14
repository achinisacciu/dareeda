import { http, connectSSEPost, BASE_URL, API_PREFIX, type ApiError, type SSEHandle } from './client'
import type { AnalysisResult, ProblemType } from '@/types/analysis'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  api/analysis.ts                                                         ║
// ║                                                                          ║
// ║  Allineato alla spec reale del backend dareeda (openapi.json):           ║
// ║    POST   /api/analysis/upload                                           ║
// ║    POST   /api/analysis/analyze/{file_id}  — SSE eventi named            ║
// ║    DELETE /api/analysis/cache/{file_id}                                   ║
// ║    POST   /api/reports/generate-pdf                                       ║
// ╚══════════════════════════════════════════════════════════════════════════╝

// ── Re-export per compatibilita con tipi gia usati nel codice ─────────────────
export type { ProblemType }

// ── Tipi di dominio ───────────────────────────────────────────────────────────

export interface AcceptedFeature {
  name:           string
  source_columns: string[]
  formula?:       string
  type?:          string
  status?:        string
}

/**
 * Contesto di analisi inviato come body JSON nella POST /analyze.
 * I nomi dei campi corrispondono esattamente a quelli attesi dal backend.
 */
export interface AnalysisContext {
  target?:             string | null
  problem_type?:       ProblemType | null
  semantic_overrides?: Record<string, string>
  selected_features?:  string[] | null
  accepted_features?:  string[] | null
  cleaning_actions?:   Record<string, unknown>[]
}

/** Risposta di POST /api/analysis/upload */
export interface UploadResponse {
  file_id:      string
  filename:     string
  file_format?: string
  n_rows?:      number | null
  n_cols?:      number | null
  columns?:     string[]
  dtypes?:      Record<string, string>
}

/**
 * Progetto in-memory (concetto frontend-only).
 * Il backend e stateless: non esiste una lista progetti lato server.
 */
export interface ProjectSummary {
  id:          string   // = file_id
  filename:    string
  file_format: string
  n_rows:      number | null
  n_cols:      number | null
  created_at:  string
  has_result:  boolean
}

export interface ProjectDetail extends ProjectSummary {
  columns?:  string[]
  dtypes?:   Record<string, string>
  context?:  AnalysisContext
}

// Backward compat: tipo usato da ReportPage legacy
export type ReportFormat = 'pdf'
export interface ReportStatus {
  project_id: string
  status:     'pending' | 'ready' | 'error'
  url?:       string
  error?:     string
  format?:    ReportFormat
}

// ── Costanti moduli ───────────────────────────────────────────────────────────

export type AnalysisModuleName =
  | 'overview'
  | 'data_quality'
  | 'univariate'
  | 'bivariate'
  | 'multivariate'
  | 'timeseries'
  | 'ml_exploratory'
  | 'insights'
  | 'enterprise'

export const ANALYSIS_MODULE_ORDER: AnalysisModuleName[] = [
  'overview',
  'data_quality',
  'univariate',
  'bivariate',
  'multivariate',
  'timeseries',
  'ml_exploratory',
  'insights',
  'enterprise',
]

// ── SSE event shapes (backend reale) ─────────────────────────────────────────

/** event: module — un modulo EDA completato */
export interface SSEModuleEvent {
  module: string
  label:  string
  data:   unknown
}

/** event: done — analisi terminata */
export interface SSEDoneEvent {
  meta?:                unknown
  feature_engineering?: unknown
  [key: string]: unknown
}

/** event: error — errore fatale dal backend */
export interface SSEErrorEvent {
  detail: string
}

// ── Upload API ────────────────────────────────────────────────────────────────
// POST /api/analysis/upload

export const uploadApi = {
  upload(file: File, onProgress?: (pct: number) => void): Promise<UploadResponse> {
    const form = new FormData()
    form.append('file', file)
    return http
      .post<UploadResponse>('/analysis/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress(e) {
          if (onProgress && e.total) {
            onProgress(Math.round((e.loaded / e.total) * 100))
          }
        },
      })
      .then((r) => r.data)
  },
}

/**
 * projectsApi — stub backward-compat.
 * La maggior parte dei metodi e no-op perche il backend e stateless.
 */
export const projectsApi = {
  list: (): Promise<ProjectSummary[]> => Promise.resolve([]),

  get: (id: string): Promise<ProjectDetail> =>
    Promise.resolve({
      id,
      filename:    '',
      file_format: 'csv',
      n_rows:      null,
      n_cols:      null,
      created_at:  new Date().toISOString(),
      has_result:  false,
    }),

  upload: (file: File, onProgress?: (pct: number) => void) =>
    uploadApi.upload(file, onProgress),

  updateContext: (_id: string, ctx: AnalysisContext): Promise<ProjectDetail> =>
    Promise.resolve({
      id:          _id,
      filename:    '',
      file_format: 'csv',
      n_rows:      null,
      n_cols:      null,
      created_at:  new Date().toISOString(),
      has_result:  false,
      context:     ctx,
    }),

  delete: (fileId: string): Promise<void> =>
    http
      .delete(`/analysis/cache/${encodeURIComponent(fileId)}`)
      .then(() => undefined),
}

// ── Analysis API ──────────────────────────────────────────────────────────────
// POST /api/analysis/analyze/{file_id}  (SSE named events via POST)
// DELETE /api/analysis/cache/{file_id}

export interface RunAnalysisCallbacks {
  onOpen?:    () => void
  onProgress: (event: SSEModuleEvent) => void
  onComplete: (result: AnalysisResult) => void
  onError:    (err: SSEErrorEvent | ApiError | { message: string }) => void
}

interface PartialResult {
  modules:              Record<string, unknown>
  meta?:                unknown
  feature_engineering?: unknown
}

export const analysisApi = {
  /**
   * Avvia l'analisi EDA via SSE (POST).
   *
   * Il backend emette eventi named:
   *   event: start               — analisi avviata
   *   event: meta                — metadati del dataset
   *   event: feature_engineering — feature engineering e cleaning
   *   event: module              — { module, label, data }  un modulo completato
   *   event: done                — analisi completata
   *   event: error               — { detail }  errore fatale
   */
  run(fileId: string, cbs: RunAnalysisCallbacks, context?: AnalysisContext): SSEHandle {
    const partial: PartialResult = { modules: {} }

    function buildResult(): AnalysisResult {
      return {
        ...(partial.modules as Partial<AnalysisResult>),
        meta:                partial.meta,
        feature_engineering: partial.feature_engineering,
      } as AnalysisResult
    }

    // Build the POST body from the analysis context
    const body: Record<string, unknown> = {
      target:             context?.target             ?? null,
      problem_type:       context?.problem_type       ?? null,
      semantic_overrides: context?.semantic_overrides  ?? {},
      selected_features:  context?.selected_features   ?? [],
      accepted_features:  context?.accepted_features   ?? [],
      cleaning_actions:   context?.cleaning_actions    ?? [],
    }

    return connectSSEPost<never>({
      path:  `/analysis/analyze/${encodeURIComponent(fileId)}`,
      body,

      events: {
        start: () => {
          cbs.onOpen?.()
        },

        meta: (raw: string) => {
          try {
            partial.meta = JSON.parse(raw)
          } catch { /* ignore */ }
        },

        feature_engineering: (raw: string) => {
          try {
            partial.feature_engineering = JSON.parse(raw)
          } catch { /* ignore */ }
        },

        module: (raw: string) => {
          try {
            const ev = JSON.parse(raw) as SSEModuleEvent
            partial.modules[ev.module] = ev.data
            cbs.onProgress(ev)
          } catch { /* frame malformato — ignora */ }
        },

        done: (_raw: string) => {
          cbs.onComplete(buildResult())
        },

        error: (raw: string) => {
          try {
            cbs.onError(JSON.parse(raw) as SSEErrorEvent)
          } catch {
            cbs.onError({ message: 'Errore del server' })
          }
        },
      },

      onError: () => {
        cbs.onError({
          message: 'Connessione SSE interrotta. Verifica la connessione e riprova.',
        })
      },
    })
  },

  /** Elimina la cache del file dal backend */
  evict(fileId: string): Promise<void> {
    return http
      .delete(`/analysis/cache/${encodeURIComponent(fileId)}`)
      .then(() => undefined)
  },

  /** Stub backward-compat — il backend e stateless */
  getResult(_id: string): Promise<AnalysisResult> {
    return Promise.reject(
      new Error('getResult non supportato: il backend e stateless'),
    )
  },

  /** Stub backward-compat — annullare chiudendo SSEHandle */
  cancel(_id: string): Promise<void> {
    return Promise.resolve()
  },
}

// ── Reports API ───────────────────────────────────────────────────────────────
// POST /api/reports/generate-pdf

export const reportsApi = {
  /**
   * Genera un PDF e lo restituisce come Blob.
   * Il backend risponde direttamente con il file binario (nessun polling necessario).
   */
  async generatePdf(analysisData: Record<string, unknown>): Promise<Blob> {
    const endpoint = `${BASE_URL}${API_PREFIX}/reports/generate-pdf`
    const response = await fetch(endpoint, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ analysis_data: analysisData }),
    })
    if (!response.ok) {
      let msg = `Errore ${response.status}`
      try {
        const j = (await response.json()) as { detail?: string }
        msg = j.detail ?? msg
      } catch { /* skip */ }
      throw new Error(msg)
    }
    return response.blob()
  },
}

/**
 * reportApi — backward compat per ReportPage legacy.
 * Non utilizzare in codice nuovo: usare reportsApi.generatePdf direttamente.
 */
export const reportApi = {
  generate: (_id: string) =>
    Promise.reject(new Error('Usa reportsApi.generatePdf')),

  status: (_id: string): Promise<ReportStatus> =>
    Promise.reject(
      new Error('status non supportato: usa reportsApi.generatePdf'),
    ),

  downloadUrl: (_id: string): string =>
    `${BASE_URL}${API_PREFIX}/reports/generate-pdf`,
}