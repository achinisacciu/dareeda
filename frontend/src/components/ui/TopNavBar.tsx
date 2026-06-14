import { useAnalysisStore } from '@/stores/analysisStore'
import { Search, Bell, Cloud, User } from 'lucide-react'

export function TopNavBar() {
  const currentProject = useAnalysisStore((s) => s.currentProject)

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-6 bg-white dark:bg-neutral-900 h-14 w-full border-b border-neutral-200 dark:border-neutral-800">
      <div className="flex items-center gap-8">
        <span className="text-[#ff3853] font-headline font-bold uppercase tracking-widest text-xs">
          Project: {currentProject?.filename ?? 'Nessun progetto'}
        </span>
        <nav className="hidden md:flex items-center gap-6">
          <span className="font-['Inter'] text-xs font-medium uppercase tracking-widest text-neutral-500">
            Analyst: User
          </span>
          <span className="font-['Inter'] text-xs font-medium uppercase tracking-widest text-neutral-500">
            Classification: Internal Only
          </span>
          <span className="font-['Inter'] text-xs font-medium uppercase tracking-widest text-neutral-500">
            Framework: EDA Standard
          </span>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative hidden sm:flex items-center text-neutral-400 focus-within:text-primary">
          <Search className="absolute left-3 w-4 h-4" />
          <input
            className="bg-[--color-surface-container-low] border-none rounded-full py-1.5 pl-9 pr-4 text-xs focus:ring-1 focus:ring-primary w-48 transition-all"
            placeholder="Search matrix..."
            type="text"
          />
        </div>
        <div className="flex items-center gap-3">
          <button className="text-neutral-400 hover:text-primary active:opacity-70 transition-colors">
            <Bell className="w-4 h-4" />
          </button>
          <button className="text-[--color-tertiary] active:opacity-70 transition-opacity">
            <Cloud className="w-4 h-4" />
          </button>
          <div className="w-8 h-8 rounded-full bg-neutral-200 overflow-hidden border border-neutral-300 flex items-center justify-center text-neutral-500 hover:bg-neutral-300 cursor-pointer transition-colors">
            <User className="w-5 h-5" />
          </div>
        </div>
      </div>
    </header>
  )
}
