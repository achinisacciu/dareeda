import { create } from 'zustand'
import {
  uploadApi,
  analysisApi,
  ANALYSIS_MODULE_ORDER,
  type ProjectSummary,
  type ProjectDetail,
  type AnalysisContext,
  type AnalysisModuleName,
  type UploadResponse,
} from '@/api/analysis'
import type { SSEHandle } from '@/api/client'
import type { AnalysisResult } from '@/types/analysis'
import { toast } from '@/stores/uiStore'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  analysisStore.ts                                                        ║
// ║                                                                          ║
// ║  Il backend dareeda è STATELESS (nessun database).                       ║
// ║  I "progetti" sono tenuti in-memory nel frontend.                        ║
// ║  Al refresh della pagina la lista si azzera.                             ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export type AnalysisStatus = 'idle' | 'running' | 'complete' | 'error'
export type UploadStatus   = 'idle' | 'uploading' | 'success' | 'error'

export interface AnalysisState {
  projects:         Record<string, ProjectSummary>
  projectIds:       string[]
  currentProject:   ProjectDetail | null
  result:           AnalysisResult | null

  analysisStatus:   AnalysisStatus
  uploadStatus:     UploadStatus
  uploadProgress:   number

  currentModule:    AnalysisModuleName | null
  currentModulePct: number
  completedModules: string[]
  moduleProgress:   Record<string, number>
  moduleMessages:   Record<string, string>

  setCurrentProject:   (project: ProjectDetail | null) => void
  loadProjects:        () => Promise<void>
  selectProject:       (projectId: string) => Promise<void>
  uploadFile:          (file: File) => Promise<void>
  deleteProject:       (projectId: string) => Promise<void>
  updateContext:       (ctx: AnalysisContext) => Promise<void>
  runAnalysis:         () => void
  cancelAnalysis:      () => void
  startProgressStream: (fileId: string, context?: AnalysisContext) => void
}

// ── Selectors ─────────────────────────────────────────────────────────────────

export function selectOverallProgress(state: AnalysisState): number {
  const n = ANALYSIS_MODULE_ORDER.length
  if (n === 0) return 0
  const total = ANALYSIS_MODULE_ORDER.reduce((sum, mod) => {
    if (typeof state.moduleProgress[mod] === 'number') return sum + state.moduleProgress[mod]
    if (state.completedModules.includes(mod)) return sum + 100
    return sum
  }, 0)
  return Math.round(total / n)
}

export function selectIsRunning(state: AnalysisState): boolean {
  return state.analysisStatus === 'running'
}

// ── Helpers ───────────────────────────────────────────────────────────────────

let _sse: SSEHandle | null = null

function uniq(arr: string[]): string[] {
  return Array.from(new Set(arr))
}

function makeProject(resp: UploadResponse): ProjectDetail {
  const ext = resp.filename?.split('.').pop()?.toLowerCase() ?? ''
  return {
    id:          resp.file_id,
    filename:    resp.filename,
    file_format: resp.file_format ?? (ext === 'parquet' ? 'parquet' : 'csv'),
    n_rows:      resp.n_rows ?? null,
    n_cols:      resp.n_cols ?? null,
    columns:     resp.columns,
    dtypes:      resp.dtypes,
    has_result:  false,
    created_at:  new Date().toISOString(),
    context:     {},
  }
}

// ── Store ─────────────────────────────────────────────────────────────────────

export const useAnalysisStore = create<AnalysisState>()((set, get) => ({
  projects:         {},
  projectIds:       [],
  currentProject:   null,
  result:           null,
  analysisStatus:   'idle',
  uploadStatus:     'idle',
  uploadProgress:   0,
  currentModule:    null,
  currentModulePct: 0,
  completedModules: [],
  moduleProgress:   {},
  moduleMessages:   {},

  setCurrentProject: (project) => set({ currentProject: project }),

  // Backend stateless — nessuna API per listare i progetti
  loadProjects: async () => { /* no-op */ },

  // Seleziona da in-memory, senza chiamate API
  selectProject: async (projectId) => {
    const { projects } = get()
    const found = projects[projectId]
    if (!found) {
      toast.error('Progetto non trovato', 'Il file potrebbe essere scaduto dalla cache del backend.')
      return
    }
    set({
      currentProject:   { ...found },
      result:           null,
      analysisStatus:   found.has_result ? 'complete' : 'idle',
      currentModule:    null,
      currentModulePct: 0,
      completedModules: found.has_result ? [...ANALYSIS_MODULE_ORDER] : [],
      moduleProgress:   found.has_result
        ? Object.fromEntries(ANALYSIS_MODULE_ORDER.map((m) => [m, 100]))
        : {},
      moduleMessages:   {},
    })
  },

  uploadFile: async (file) => {
    set({ uploadStatus: 'uploading', uploadProgress: 0 })
    try {
      const resp    = await uploadApi.upload(file, (pct) => set({ uploadProgress: pct }))
      const project = makeProject(resp)
      set((state) => {
        const projects = { ...state.projects, [resp.file_id]: project }
        const projectIds = [resp.file_id, ...state.projectIds.filter((id) => id !== resp.file_id)]
        return {
          uploadStatus:     'success',
          uploadProgress:   100,
          currentProject:   project,
          result:           null,
          analysisStatus:   'idle',
          currentModule:    null,
          currentModulePct: 0,
          completedModules: [],
          moduleProgress:   {},
          moduleMessages:   {},
          projects,
          projectIds,
        }
      })
      toast.success('File caricato', resp.filename)
    } catch (err) {
      set({ uploadStatus: 'error', uploadProgress: 0 })
      const msg = err instanceof Error ? err.message : 'Verifica il formato del file e riprova.'
      toast.error('Upload fallito', msg)
      throw err
    }
  },

  deleteProject: async (projectId) => {
    // Evict dalla cache backend (ignora errori se già scaduto)
    analysisApi.evict(projectId).catch(() => undefined)
    set((state) => {
      const isCurrent = state.currentProject?.id === projectId
      const projects = { ...state.projects }
      delete projects[projectId]
      const projectIds = state.projectIds.filter((id) => id !== projectId)
      return {
        projects,
        projectIds,
        currentProject:   isCurrent ? null   : state.currentProject,
        result:           isCurrent ? null   : state.result,
        analysisStatus:   isCurrent ? 'idle' : state.analysisStatus,
        currentModule:    isCurrent ? null   : state.currentModule,
        currentModulePct: isCurrent ? 0      : state.currentModulePct,
        completedModules: isCurrent ? []     : state.completedModules,
        moduleProgress:   isCurrent ? {}     : state.moduleProgress,
        moduleMessages:   isCurrent ? {}     : state.moduleMessages,
      }
    })
  },

  // Backend stateless — contesto salvato solo in-memory
  updateContext: async (ctx) => {
    const { currentProject, projects } = get()
    if (!currentProject) { toast.error('Nessun progetto selezionato'); return }
    const updated: ProjectDetail = {
      ...currentProject,
      context: { ...currentProject.context, ...ctx },
    }
    set((state) => ({
      currentProject: updated,
      projects: {
        ...state.projects,
        [updated.id]: { ...state.projects[updated.id], context: updated.context },
      },
    }))
  },

  runAnalysis: () => {
    const { currentProject } = get()
    if (!currentProject) {
      toast.error('Nessun progetto selezionato', 'Carica un file per continuare.')
      return
    }
    get().startProgressStream(currentProject.id, currentProject.context)
  },

  cancelAnalysis: () => {
    _sse?.close()
    _sse = null
    set({ analysisStatus: 'idle', currentModule: null, currentModulePct: 0 })
    toast.info('Analisi annullata')
  },

  startProgressStream: (fileId, context = {}) => {
    _sse?.close()
    _sse = null
    set({
      analysisStatus:   'running',
      result:           null,
      currentModule:    null,
      currentModulePct: 0,
      completedModules: [],
      moduleProgress:   {},
      moduleMessages:   {},
    })

    _sse = analysisApi.run(fileId, {
      onOpen: () => undefined,

      onProgress: (event) => {
        const mod = event.module as AnalysisModuleName
        set((state) => ({
          currentModule:    mod,
          currentModulePct: 100,
          completedModules: uniq([...state.completedModules, mod]),
          moduleProgress:   { ...state.moduleProgress, [mod]: 100 },
          moduleMessages:   { ...state.moduleMessages, [mod]: event.label },
        }))
      },

      onComplete: (result) => {
        _sse = null
        set((state) => {
          const hasCurrent = state.currentProject?.id === fileId
          const projects = { ...state.projects }
          if (projects[fileId]) {
            projects[fileId] = { ...(projects[fileId] as ProjectSummary), has_result: true }
          }
          return {
            analysisStatus:   'complete',
            result,
            currentModule:    null,
            currentModulePct: 100,
            completedModules: uniq([...state.completedModules, ...ANALYSIS_MODULE_ORDER]),
            moduleProgress:   Object.fromEntries(ANALYSIS_MODULE_ORDER.map((m) => [m, 100])),
            currentProject: hasCurrent && state.currentProject
              ? { ...state.currentProject, has_result: true }
              : state.currentProject,
            projects,
          }
        })
        toast.success('Analisi completata')
      },

      onError: (err) => {
        _sse = null
        const message =
          'detail'  in (err as object) ? (err as { detail: string }).detail  :
          'message' in (err as object) ? (err as { message: string }).message :
          "Errore durante l'analisi"
        set({ analysisStatus: 'error', currentModule: null })
        toast.error('Analisi fallita', message)
      },
    }, context)
  },
}))
