import { create } from 'zustand'

const useDatasetStore = create((set) => ({
  activeDataset: null,
  setActiveDataset: (ds) => set({ activeDataset: ds }),
  clearDataset: () => set({ activeDataset: null }),
}))

export default useDatasetStore
