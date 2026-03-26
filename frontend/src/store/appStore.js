import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAppStore = create(persist(
  (set) => ({
    sidebarExpanded: true,
    toggleSidebar: () => set(s => ({ sidebarExpanded: !s.sidebarExpanded })),
  }),
  { name: 'dareeda-app-store' }
))

export default useAppStore
