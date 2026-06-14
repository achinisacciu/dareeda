import { type ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { TopNavBar } from './TopNavBar'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[--color-surface-container-lowest] text-[--color-on-surface] flex">
      {/* ── Sidebar (Fixed left) ──────────────────────────────── */}
      <Sidebar />

      {/* ── Main content area ─────────────────────────────────── */}
      <main className="ml-64 flex-1 flex flex-col min-h-screen">
        <TopNavBar />
        
        <div id="main-content" className="flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

