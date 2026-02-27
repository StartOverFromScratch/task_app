import type { Task } from './task'

export type CarryoverAction = 'today' | 'plus_2d' | 'plus_7d' | 'needs_redefine'

export interface CarryoverCandidate extends Task {
  overdue_days: number
}

export interface StaleTask extends Task {
  stale_days: number
  threshold_days: number
}

export interface CarryoverRequest {
  action: CarryoverAction
}
