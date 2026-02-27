import type { CarryoverCandidate, CarryoverRequest } from '~/types/carryover'
import type { Task } from '~/types/task'

export const carryoverRepository = {
  async fetchCandidates(): Promise<CarryoverCandidate[]> {
    return await $fetch('/tasks/carryover-candidates', { baseURL: useRuntimeConfig().public.apiBase })
  },

  async doCarryover(taskId: number, body: CarryoverRequest): Promise<Task> {
    return await $fetch(`/tasks/${taskId}/carryover`, { method: 'POST', baseURL: useRuntimeConfig().public.apiBase, body })
  }
}
