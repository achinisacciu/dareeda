import { useAnalysisStore } from '@/stores/analysisStore'
import { Search, Bell, Cloud, User } from 'lucide-react'

export function TopNavBar() {
  const currentProject = useAnalysisStore((s) => s.currentProject)

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-6 h-14 w-full border-b border-[--color-divider] bg-[--color-surface-glass] backdrop-blur-md">
      <div className="flex items-center gap-8">
        <span className="font-headline font-bold uppercase tracking-widest text-xs text-[--color-text-muted]">
          Project: <span className="text-[--color-text]">{currentProject?.filename ?? 'Nessun progetto'}</span>
        </span>
        <nav className="hidden lg:flex items-center gap-6">
          <span className="font-body text-xs font-medium uppercase tracking-widest text-[--color-text-faint]">
            Analyst: <span className="text-[--color-text-muted]">User</span>
          </span>
          <span className="font-body text-xs font-medium uppercase tracking-widest text-[--color-text-faint]">
            Classification: <span className="text-[--color-text-muted]">Internal Only</span>
          </span>
          <span className="font-body text-xs font-medium uppercase tracking-widest text-[--color-text-faint]">
            Framework: <span className="text-[--color-text-muted]">EDA Standard</span>
          </span>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative hidden sm:flex items-center transition-colors focus-within:text-[--color-primary]">
          <Search className="absolute left-3 w-4 h-4 text-[--color-text-muted]" />
          <input
            className="w-48 rounded-full bg-[--color-surface-2] border-none py-1.5 pl-9 pr-4 text-xs font-medium placeholder:text-[--color-text-faint] focus:ring-2 focus:ring-[--color-primary] transition-all"
            placeholder="Cerca nel progetto..."
            type="text"
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            className="text-[--color-text-muted] hover:text-[--color-text] active:opacity-70 transition-colors"
            aria-label="Notifiche"
          >
            <Bell className="w-4 h-4" />
          </button>
          <button
            className="text-[--color-text-muted] hover:text-[--color-text] active:opacity-70 transition-colors"
            aria-label="Sync cloud"
          >
            <Cloud className="w-4 h-4" />
          </button>
          <div
            className="w-8 h-8 rounded-full bg-[--color-surface-offset] border border-[--color-divider] flex items-center justify-center text-[--color-text-muted] hover:bg-[--color-surface-2] hover:text-[--color-text] cursor-pointer transition-colors"
            role="button"
            tabIndex={0}
            aria-label="Profilo utente"
          >
            <User className="w-5 h-5" />
          </div>
        </div>
      </div>
    </header>
  )
}