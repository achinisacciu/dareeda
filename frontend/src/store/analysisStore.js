import { create } from 'zustand'

const useAnalysisStore = create((set) => ({
  analysisResult: null,
  activeSection: 'overview',
  setAnalysisResult: (r) => set({ analysisResult: r }),
  setActiveSection: (s) => set({ activeSection: s }),
}))

export default useAnalysisStore
