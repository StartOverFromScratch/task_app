export interface CaptureItem {
  id: number
  text: string
  related_task_id: number | null
  created_at: string
  is_resolved: boolean
}

export interface CaptureCreateRequest {
  text: string
  related_task_id?: number | null
}

export interface CaptureUpdateRequest {
  text?: string
  is_resolved?: boolean
  related_task_id?: number | null
}
