import { defineStore } from 'pinia'
import type { CarryoverCandidate } from '~/types/carryover'

export const useCarryoverStore = defineStore('carryover', () => {
  const candidates = ref<CarryoverCandidate[]>([])

  function setAll(list: CarryoverCandidate[]) {
    candidates.value = list
  }

  function removeCandidate(id: number) {
    candidates.value = candidates.value.filter(t => t.id !== id)
  }

  return { candidates, setAll, removeCandidate }
})
