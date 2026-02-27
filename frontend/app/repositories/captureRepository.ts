import type { CaptureItem, CaptureCreateRequest, CaptureUpdateRequest } from '~/types/capture'

export const captureRepository = {
  async fetchAll(isResolved?: boolean): Promise<CaptureItem[]> {
    return await $fetch('/captures', {
      baseURL: useRuntimeConfig().public.apiBase,
      params: isResolved !== undefined ? { is_resolved: isResolved } : undefined
    })
  },

  async create(body: CaptureCreateRequest): Promise<CaptureItem> {
    return await $fetch('/captures', { method: 'POST', baseURL: useRuntimeConfig().public.apiBase, body })
  },

  async update(id: number, body: CaptureUpdateRequest): Promise<CaptureItem> {
    return await $fetch(`/captures/${id}`, { method: 'PATCH', baseURL: useRuntimeConfig().public.apiBase, body })
  },

  async remove(id: number): Promise<void> {
    return await $fetch(`/captures/${id}`, { method: 'DELETE', baseURL: useRuntimeConfig().public.apiBase })
  }
}
