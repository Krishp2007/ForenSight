import useCaseStore from '../store/caseStore'

const useCase = () => {
  const cases = useCaseStore((s) => s.cases)
  const activeCase = useCaseStore((s) => s.activeCase)
  const setCases = useCaseStore((s) => s.setCases)
  const setActiveCase = useCaseStore((s) => s.setActiveCase)
  const clearActiveCase = useCaseStore((s) => s.clearActiveCase)
  const updateCaseInList = useCaseStore((s) => s.updateCaseInList)

  return { cases, activeCase, setCases, setActiveCase, clearActiveCase, updateCaseInList }
}

export default useCase
