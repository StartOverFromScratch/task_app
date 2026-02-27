import type { Priority } from '~/types/task'

export const STALE_THRESHOLD: Record<Priority, number> = {
  must: 7,
  should: 21
}

export function getStaleDays(lastUpdatedAt: string): number {
  const diff = Date.now() - new Date(lastUpdatedAt).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
}

export function isStale(lastUpdatedAt: string, priority: Priority): boolean {
  return getStaleDays(lastUpdatedAt) >= STALE_THRESHOLD[priority]
}
