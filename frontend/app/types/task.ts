export type TaskType = 'research' | 'decision' | 'execution'
export type TaskStatus = 'todo' | 'doing' | 'done' | 'carryover_candidate' | 'needs_redefine' | 'snoozed'
export type Priority = 'must' | 'should'

export interface Task {
  id: number
  title: string
  task_type: TaskType
  category: string | null
  priority: Priority
  status: TaskStatus
  due_date: string | null
  parent_id: number | null
  done_criteria: string
  decision_criteria: string | null
  reversible: boolean | null
  exploration_limit: number | null
  origin_checklist_item_id: number | null
  last_updated_at: string
  created_at: string
}

export interface TaskDetail extends Task {
  children: Task[]
  checklist: ChecklistItem[]
  origin: OriginInfo | null
}

export interface OriginInfo {
  parent_task_id: number
  parent_task_title: string
  checklist_item_text: string
}

export interface ChecklistItem {
  id: number
  task_id: number
  text: string
  is_done: boolean
  order_no: number
  extracted_task_id: number | null
}

export interface TaskCreateRequest {
  title: string
  task_type: TaskType
  category?: string | null
  priority: Priority
  due_date?: string | null
  parent_id?: number | null
  done_criteria: string
  decision_criteria?: string | null
  reversible?: boolean | null
  exploration_limit?: number | null
}

export interface TaskUpdateRequest {
  title?: string
  task_type?: TaskType
  category?: string | null
  priority?: Priority
  status?: Exclude<TaskStatus, 'done'>
  due_date?: string | null
  done_criteria?: string
  decision_criteria?: string | null
  reversible?: boolean | null
  exploration_limit?: number | null
}

export interface TaskQueryParams {
  status?: TaskStatus
  task_type?: TaskType
  priority?: Priority
  parent_id?: number | null
}

export interface ConvergenceChecklist {
  options_within_limit: boolean
  structure_simplified: boolean
  reversible_confirmed: boolean
}

export interface ConvergenceInfo {
  task_id: number
  exploration_limit: number | null
  exploration_used: number
  exploration_remaining: number | null
  reversible: boolean | null
  decision_criteria: string | null
  is_convergeable: boolean
  convergence_checklist: ConvergenceChecklist
}
