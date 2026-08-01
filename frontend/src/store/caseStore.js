import { create } from 'zustand'

const useCaseStore = create((set) => ({
  cases: [],
  activeCase: null,

  setCases: (cases) => set({ cases }),
  setActiveCase: (c) => set({ activeCase: c }),
  clearActiveCase: () => set({ activeCase: null }),

  updateCaseInList: (updated) =>
    set((state) => ({
      cases: state.cases.map((c) => (c.id === updated.id ? updated : c)),
      activeCase: state.activeCase?.id === updated.id ? updated : state.activeCase,
    })),
}))

export default useCaseStore
