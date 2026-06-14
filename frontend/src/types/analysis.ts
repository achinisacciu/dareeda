// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  types/analysis.ts — tutti i tipi TypeScript del dominio analisi        ║
// ║  Nessuna dipendenza interna (leaf module).                               ║
// ╚══════════════════════════════════════════════════════════════════════════╝

// ── Enums di dominio ──────────────────────────────────────────────────────────

export type ProblemType = 'classification' | 'regression'

export type SemanticType =
  | 'numeric_continuous'
  | 'numeric_discrete'
  | 'categorical'
  | 'datetime'
  | 'text'
  | 'boolean'
  | 'identifier'
  | 'constant'
  | 'unknown'

// ── Plotly figure ─────────────────────────────────────────────────────────────

export interface PlotlyFigure {
  data:    unknown[]
  layout:  Record<string, unknown>
  config?: Record<string, unknown>
}

// ── Overview module ───────────────────────────────────────────────────────────

export interface GroupsCount {
  numeric_continuous?: number
  numeric_discrete?:   number
  categorical?:        number
  datetime?:           number
  text?:               number
  boolean?:            number
  identifier?:         number
  constant?:           number
}

export interface ColumnOverview {
  name:           string
  semantic_type:  SemanticType | string
  dtype:          string
  n_unique?:      number
  missing_pct?:   number
  n_missing?:     number
  sample_values?: unknown[]
}

export interface Overview {
  n_rows:        number
  n_cols:        number
  missing_pct:   number
  n_missing:     number
  duplicate_pct: number
  n_duplicates:  number
  memory_human?: string
  memory_mb?:    number
  groups_count?: GroupsCount
  columns?:      ColumnOverview[]
}

// ── Data quality module ───────────────────────────────────────────────────────

export interface DQIssueAction {
  type:    string
  column?: string | null
  params?: Record<string, unknown>
}

export interface DQStandardizedIssue {
  column:      string | null
  issue_type:  string
  severity:    'high' | 'medium' | 'low'
  description: string
  action:      DQIssueAction
}

export interface DQMissing {
  total_missing_cells?: number
  missing_by_column?:   Record<string, number>
  missing_heatmap?:     PlotlyFigure
}

export interface DQDuplicates {
  n_duplicates?:    number
  duplicate_ratio?: number
}

export interface DQOutliers {
  n_outliers?:    number
  outlier_ratio?: number
  by_column?:     Record<string, number>
}

export interface DataQuality {
  missing?:             DQMissing
  duplicates?:          DQDuplicates
  outliers?:            DQOutliers
  standardized_issues?: DQStandardizedIssue[]
  charts?:              Record<string, PlotlyFigure>
}

// ── Univariate module ─────────────────────────────────────────────────────────

export interface UnivariateColumnResult {
  semantic_type?: SemanticType | string
  charts?:        Record<string, PlotlyFigure>
  stats?:         Record<string, unknown>
  ai_comment?:    string
}

// ── Moduli aperti ─────────────────────────────────────────────────────────────

export type BivariateResult     = Record<string, unknown>
export type MultivariateResult  = Record<string, unknown>
export type TimeseriesResult    = Record<string, unknown>
export type MlExploratoryResult = Record<string, unknown>
export type EnterpriseResult    = Record<string, unknown>
export type InsightsResult      = unknown

// ── AnalysisResult ────────────────────────────────────────────────────────────
// Accumulato durante lo streaming SSE.
// Tutti i campi sono opzionali: i moduli arrivano uno alla volta.

export interface AnalysisResult {
  overview?:            Overview
  data_quality?:        DataQuality
  univariate?:          Record<string, UnivariateColumnResult>
  bivariate?:           BivariateResult
  multivariate?:        MultivariateResult
  timeseries?:          TimeseriesResult
  ml_exploratory?:      MlExploratoryResult
  enterprise?:          EnterpriseResult
  insights?:            InsightsResult
  /** Metadati del run — da evento SSE `done` */
  meta?:                unknown
  /** Feature engineering — da evento SSE `done` */
  feature_engineering?: unknown
}

// ── Re-export per componenti che importano solo da @/types ────────────────────

export type {
  ProjectSummary,
  ProjectDetail,
  AcceptedFeature,
  AnalysisContext,
  UploadResponse,
} from '@/api/analysis'
