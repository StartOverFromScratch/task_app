import type { Task, TaskDetail, TaskCreateRequest, TaskUpdateRequest, TaskQueryParams, ConvergenceInfo } from '~/types/task'
import type { CompletionLog, CompleteRequest } from '~/types/completion'

export const taskRepository = {
  async fetchAll(params?: TaskQueryParams): Promise<Task[]> {
    return await $fetch('/tasks', { baseURL: useRuntimeConfig().public.apiBase, params })
  },

  async fetchById(id: number): Promise<TaskDetail> {
    return await $fetch(`/tasks/${id}`, { baseURL: useRuntimeConfig().public.apiBase })
  },

  async create(body: TaskCreateRequest): Promise<Task> {
    return await $fetch('/tasks', { method: 'POST', baseURL: useRuntimeConfig().public.apiBase, body })
  },

  async update(id: number, body: TaskUpdateRequest): Promise<Task> {
    return await $fetch(`/tasks/${id}`, { method: 'PATCH', baseURL: useRuntimeConfig().public.apiBase, body })
  },

  async remove(id: number): Promise<void> {
    return await $fetch(`/tasks/${id}`, { method: 'DELETE', baseURL: useRuntimeConfig().public.apiBase })
  },

  async complete(id: number, body: CompleteRequest = {}): Promise<CompletionLog> {
    return await $fetch(`/tasks/${id}/complete`, { method: 'POST', baseURL: useRuntimeConfig().public.apiBase, body })
  },

  async fetchCompletionLog(id: number): Promise<CompletionLog[]> {
    return await $fetch(`/tasks/${id}/completion-log`, { baseURL: useRuntimeConfig().public.apiBase })
  },

  async fetchChildren(id: number): Promise<Task[]> {
    return await $fetch(`/tasks/${id}/children`, { baseURL: useRuntimeConfig().public.apiBase })
  },

  async createChild(id: number, body: TaskCreateRequest): Promise<Task> {
    return await $fetch(`/tasks/${id}/children`, { method: 'POST', baseURL: useRuntimeConfig().public.apiBase, body })
  },

  async fetchConvergence(id: number): Promise<ConvergenceInfo> {
    return await $fetch(`/tasks/${id}/convergence`, { baseURL: useRuntimeConfig().public.apiBase })
  },

  async fetchStale(priority?: 'must' | 'should'): Promise<import('~/types/carryover').StaleTask[]> {
    return await $fetch('/tasks/stale', { baseURL: useRuntimeConfig().public.apiBase, params: priority ? { priority } : undefined })
  }
}
