import type { Task, TaskDetail, TaskCreateRequest, TaskUpdateRequest, TaskQueryParams, ConvergenceInfo } from '~/types/task'
import type { CompletionLog, CompleteRequest } from '~/types/completion'

export const taskRepository = {
  async fetchAll(params?: TaskQueryParams): Promise<Task[]> {
    return await $fetch('/tasks', { baseURL: useApiBase(), params })
  },

  async fetchById(id: number): Promise<TaskDetail> {
    return await $fetch(`/tasks/${id}`, { baseURL: useApiBase() })
  },

  async create(body: TaskCreateRequest): Promise<Task> {
    return await $fetch('/tasks', { method: 'POST', baseURL: useApiBase(), body })
  },

  async update(id: number, body: TaskUpdateRequest): Promise<Task> {
    return await $fetch(`/tasks/${id}`, { method: 'PATCH', baseURL: useApiBase(), body })
  },

  async remove(id: number): Promise<void> {
    return await $fetch(`/tasks/${id}`, { method: 'DELETE', baseURL: useApiBase() })
  },

  async complete(id: number, body: CompleteRequest = {}): Promise<CompletionLog> {
    return await $fetch(`/tasks/${id}/complete`, { method: 'POST', baseURL: useApiBase(), body })
  },

  async fetchCompletionLog(id: number): Promise<CompletionLog[]> {
    return await $fetch(`/tasks/${id}/completion-log`, { baseURL: useApiBase() })
  },

  async fetchChildren(id: number): Promise<Task[]> {
    return await $fetch(`/tasks/${id}/children`, { baseURL: useApiBase() })
  },

  async createChild(id: number, body: TaskCreateRequest): Promise<Task> {
    return await $fetch(`/tasks/${id}/children`, { method: 'POST', baseURL: useApiBase(), body })
  },

  async fetchConvergence(id: number): Promise<ConvergenceInfo> {
    return await $fetch(`/tasks/${id}/convergence`, { baseURL: useApiBase() })
  },

  async fetchStale(priority?: 'must' | 'should'): Promise<import('~/types/carryover').StaleTask[]> {
    return await $fetch('/tasks/stale', { baseURL: useApiBase(), params: priority ? { priority } : undefined })
  }
}
