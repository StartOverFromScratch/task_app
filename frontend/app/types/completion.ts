export interface CompleteRequest {
  note?: string
}

export interface CompletionLog {
  id: number
  task_id: number
  completed_at: string
  note: string | null
}
