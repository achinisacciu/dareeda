import { create } from 'zustand'

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  uiStore.ts — stato UI globale                                           ║
// ║                                                                          ║
// ║  Esporta (contratto usato dai componenti già consegnati):                ║
// ║    Tipi:    Page, AnalysisTab, Theme, ModalId                            ║
// ║    Hook:    useUIStore                                                   ║
// ║    Helper:  toast                                                        ║
// ║    Selector: selectThemeResolved                                         ║
// ╚══════════════════════════════════════════════════════════════════════════╝

// ── Tipi di dominio ───────────────────────────────────────────────────────────

export type Page =
  | 'upload'
  | 'analysis'
  | 'report'

export type AnalysisTab =
  | 'overview'
  | 'data_quality'
  | 'univariate'
  | 'bivariate'
  | 'multivariate'
  | 'timeseries'
  | 'ml_exploratory'
  | 'enterprise'
  | 'insights'

export type Theme = 'light' | 'dark' | 'system'

export type ModalId =
  | 'delete_project'
  | 'context_config'
  | 'run_confirm'
  | 'cleaning_preview'
  | 'report_sections'

// ── Toast ─────────────────────────────────────────────────────────────────────

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id:       string
  variant:  ToastVariant
  title:    string
  message?: string
}

// ── State shape ───────────────────────────────────────────────────────────────

export interface UIState {
  // Navigazione
  activePage:        Page
  activeTab:         AnalysisTab
  activeColumn:      string | null

  // Modal
  modal:             { id: ModalId; data?: unknown } | null

  // Tema
  theme:             Theme

  // Sidebar
  sidebarOpen:       boolean   // mobile overlay
  sidebarCollapsed:  boolean   // desktop collapsed

  // Toast queue
  toasts:            ToastItem[]

  // Actions
  setActivePage:      (page: Page) => void
  setActiveTab:       (tab: AnalysisTab) => void
  setActiveColumn:    (col: string | null) => void

  openModal:          (id: ModalId, data?: unknown) => void
  closeModal:         () => void

  setTheme:           (theme: Theme) => void

  setSidebarOpen:     (open: boolean) => void
  toggleSidebar:      () => void
  setSidebarCollapsed:(collapsed: boolean) => void

  addToast:           (item: Omit<ToastItem, 'id'>) => void
  removeToast:        (id: string) => void
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function uid(): string {
  return Math.random().toString(36).slice(2, 9)
}

/**
 * Applica il tema all'elemento <html> come data-theme attribute.
 * Rispetta prefers-color-scheme quando theme === 'system'.
 */
function applyThemeToDom(theme: Theme): void {
  const resolved =
    theme === 'system'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      : theme
  document.documentElement.setAttribute('data-theme', resolved)
}

// ── Store ─────────────────────────────────────────────────────────────────────

export const useUIStore = create<UIState>()((set, get) => ({
  activePage:       'upload',
  activeTab:        'overview',
  activeColumn:     null,
  modal:            null,
  theme:            'system',
  sidebarOpen:      false,
  sidebarCollapsed: false,
  toasts:           [],

  setActivePage: (page) => set({ activePage: page }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  setActiveColumn: (col) => set({ activeColumn: col }),

  openModal: (id, data) => set({ modal: { id, data } }),

  closeModal: () => set({ modal: null }),

  setTheme: (theme) => {
    applyThemeToDom(theme)
    set({ theme })
  },

  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  addToast: (item) => {
    const id = uid()
    set((s) => ({ toasts: [...s.toasts, { ...item, id }] }))
    // Auto-dismiss dopo 4 s
    setTimeout(() => get().removeToast(id), 4_000)
  },

  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))

// ── Selector: tema risolto ─────────────────────────────────────────────────────
// Usato da PlotlyChart e da chiunque debba sapere il tema effettivo
// (light | dark), risolvendo 'system' via matchMedia.

export function selectThemeResolved(state: UIState): 'light' | 'dark' {
  if (state.theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'
  }
  return state.theme
}

// ── Toast helper (API imperativa) ──────────────────────────────────────────────
// Usabile fuori dai componenti React (es. negli store, nelle callback API).
//
// Uso:
//   import { toast } from '@/stores/uiStore'
//   toast.success('File caricato', 'Pokemon.csv')

export const toast = {
  success: (title: string, message?: string) =>
    useUIStore.getState().addToast({ variant: 'success', title, message }),

  error: (title: string, message?: string) =>
    useUIStore.getState().addToast({ variant: 'error', title, message }),

  warning: (title: string, message?: string) =>
    useUIStore.getState().addToast({ variant: 'warning', title, message }),

  info: (title: string, message?: string) =>
    useUIStore.getState().addToast({ variant: 'info', title, message }),
}
