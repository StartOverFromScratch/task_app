import type { CarryoverAction } from '~/types/carryover'

export function useCarryover() {
  const carryoverStore = useCarryoverStore()
  const taskStore = useTaskStore()
  const { handle } = useErrorToast()
  const toast = useToast()

  async function fetchCandidates() {
    try {
      const list = await carryoverRepository.fetchCandidates()
      carryoverStore.setAll(list)
    } catch (e) { handle(e) }
  }

  async function doCarryover(taskId: number, action: CarryoverAction) {
    try {
      const updated = await carryoverRepository.doCarryover(taskId, { action })
      carryoverStore.removeCandidate(taskId)
      taskStore.upsert(updated)
      toast.add({ title: '繰り越し処理を実行しました', color: 'success' })
    } catch (e) { handle(e) }
  }

  return { fetchCandidates, doCarryover }
}
