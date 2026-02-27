import { defineStore } from 'pinia'
import type { CaptureItem } from '~/types/capture'

export const useCaptureStore = defineStore('capture', () => {
  const items = ref<CaptureItem[]>([])
  const unresolved = computed(() => items.value.filter(i => !i.is_resolved))
  const resolved = computed(() => items.value.filter(i => i.is_resolved))

  function setAll(list: CaptureItem[]) {
    items.value = list
  }

  function upsert(item: CaptureItem) {
    const idx = items.value.findIndex(i => i.id === item.id)
    if (idx >= 0) items.value[idx] = item
    else items.value.unshift(item)
  }

  function remove(id: number) {
    items.value = items.value.filter(i => i.id !== id)
  }

  return { items, unresolved, resolved, setAll, upsert, remove }
})
