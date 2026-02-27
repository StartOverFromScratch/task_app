import type { ChecklistItem, Task, TaskType, Priority } from './task'

export type { ChecklistItem }

export interface ChecklistItemCreate {
  text: string
  order_no?: number
}

export interface ChecklistItemUpdate {
  is_done?: boolean
  text?: string
}

export interface ExtractRequest {
  title?: string | null
  task_type?: TaskType
  priority?: Priority | null
  due_date?: string | null
  done_criteria?: string | null
}

export interface ExtractResponse {
  extracted_task: Task
  checklist_item: ChecklistItem
}
