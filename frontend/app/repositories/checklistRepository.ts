import type { ChecklistItem, ChecklistItemCreate, ChecklistItemUpdate, ExtractResponse, ExtractRequest } from '~/types/checklist'

export const checklistRepository = {
  async fetchAll(taskId: number): Promise<ChecklistItem[]> {
    return await $fetch(`/tasks/${taskId}/checklist`, { baseURL: useApiBase() })
  },

  async create(taskId: number, body: ChecklistItemCreate): Promise<ChecklistItem> {
    return await $fetch(`/tasks/${taskId}/checklist`, { method: 'POST', baseURL: useApiBase(), body })
  },

  async update(taskId: number, itemId: number, body: ChecklistItemUpdate): Promise<ChecklistItem> {
    return await $fetch(`/tasks/${taskId}/checklist/${itemId}`, { method: 'PATCH', baseURL: useApiBase(), body })
  },

  async extract(taskId: number, itemId: number, body: ExtractRequest = {}): Promise<ExtractResponse> {
    return await $fetch(`/tasks/${taskId}/checklist/${itemId}/extract`, { method: 'POST', baseURL: useApiBase(), body })
  }
}
