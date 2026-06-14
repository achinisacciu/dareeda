import { useEffect, lazy, Suspense } from 'react'
import { useUIStore }       from '@/stores/uiStore'
import { useAnalysisStore } from '@/stores/analysisStore'
import { AppShell }         from '@/components/ui/AppShell'
import { ToastContainer }   from '@/components/ui/ToastContainer'
import { ModalRenderer }    from '@/components/ui/ModalRenderer'

// ── Lazy-load pages ────────────────────────────────────────────────────────────
const UploadPage   = lazy(() => import('@/pages/UploadPage'))
const AnalysisPage = lazy(() => import('@/pages/AnalysisPage'))
const ReportPage   = lazy(() => import('@/pages/ReportPage'))

// ── Page loader skeleton ───────────────────────────────────────────────────────
function PageSkeleton() {
  return (
    <div className="h-full flex flex-col gap-[--space-4] p-[--space-6] animate-pulse">
      <div className="skeleton skeleton-heading w-48" />
      <div className="grid grid-cols-3 gap-[--space-3]">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton h-20 rounded-[--radius-lg]" />
        ))}
      </div>
      <div className="skeleton flex-1 rounded-[--radius-lg]" />
    </div>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  App root                                                                ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export default function App() {
  const activePage   = useUIStore((s) => s.activePage)
  const theme        = useUIStore((s) => s.theme)

  // ── Sync theme → <html data-theme="..."> ──────────────────────────────────
  useEffect(() => {
    const root = document.documentElement

    if (theme === 'system') {
      const mq    = window.matchMedia('(prefers-color-scheme: dark)')
      const apply = (dark: boolean) => root.setAttribute('data-theme', dark ? 'dark' : 'light')
      apply(mq.matches)
      const handler = (e: MediaQueryListEvent) => {
        if (useUIStore.getState().theme === 'system') apply(e.matches)
      }
      mq.addEventListener('change', handler)
      return () => mq.removeEventListener('change', handler)
    } else {
      root.setAttribute('data-theme', theme)
    }
  }, [theme])


  // ── Reconnect SSE se analisi era in corso ──────────────────────────────────
  useEffect(() => {
    const { analysisStatus, currentProject, startProgressStream } =
      useAnalysisStore.getState()
    if (analysisStatus === 'running' && currentProject) {
      startProgressStream(currentProject.id)
    }
  }, [])

  return (
    <>
      {/* ── A11y: skip to content ────────────────────────────────────────── */}
      <a
        href="#main-content"
        className={[
          'sr-only focus:not-sr-only',
          'fixed top-[--space-2] left-1/2 -translate-x-1/2 z-[100]',
          'px-[--space-4] py-[--space-2] rounded-[--radius-md]',
          'bg-[--color-primary] text-[--color-text-inverse]',
          'text-[length:--text-sm] font-semibold shadow-[--shadow-lg]',
        ].join(' ')}
      >
        Salta al contenuto
      </a>

      {/* ── AppShell: sidebar + main ─────────────────────────────────────── */}
      <AppShell>
        <Suspense fallback={<PageSkeleton />}>
          {activePage === 'upload'   && <UploadPage />}
          {activePage === 'analysis' && <AnalysisPage />}
          {activePage === 'report'   && <ReportPage />}
        </Suspense>
      </AppShell>

      {/* ── Portal components ────────────────────────────────────────────── */}
      <ToastContainer />
      <ModalRenderer />
    </>
  )
}
