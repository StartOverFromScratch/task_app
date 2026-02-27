import type { ChecklistItemCreate, ChecklistItemUpdate, ExtractRequest } from '~/types/checklist'
import type { TaskDetail } from '~/types/task'

export function useChecklist() {
  const taskStore = useTaskStore()
  const { handle } = useErrorToast()
  const toast = useToast()

  function refreshCurrentTask(taskId: number) {
    taskRepository.fetchById(taskId)
      .then((t: TaskDetail) => { taskStore.currentTask = t })
      .catch(() => {})
  }

  async function createItem(taskId: number, data: ChecklistItemCreate) {
    try {
      await checklistRepository.create(taskId, data)
      refreshCurrentTask(taskId)
    } catch (e) { handle(e) }
  }

  async function updateItem(taskId: number, itemId: number, data: ChecklistItemUpdate) {
    try {
      await checklistRepository.update(taskId, itemId, data)
      refreshCurrentTask(taskId)
    } catch (e) { handle(e) }
  }

  async function extractItem(taskId: number, itemId: number, data: ExtractRequest = {}) {
    try {
      const result = await checklistRepository.extract(taskId, itemId, data)
      refreshCurrentTask(taskId)
      toast.add({ title: `「${result.extracted_task.title}」として切り出しました`, color: 'success' })
      return result
    } catch (e) { handle(e) }
  }

  return { createItem, updateItem, extractItem }
}
