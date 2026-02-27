import type { TaskQueryParams, TaskCreateRequest, TaskUpdateRequest } from '~/types/task'

export function useTask() {
  const taskStore = useTaskStore()
  const { handle } = useErrorToast()
  const toast = useToast()
  const router = useRouter()

  async function fetchTasks(params?: TaskQueryParams) {
    try {
      const tasks = await taskRepository.fetchAll(params)
      taskStore.setAll(tasks)
    } catch (e) { handle(e) }
  }

  async function fetchTask(id: number) {
    try {
      const task = await taskRepository.fetchById(id)
      taskStore.currentTask = task
    } catch (e) { handle(e) }
  }

  async function createTask(data: TaskCreateRequest) {
    try {
      const task = await taskRepository.create(data)
      taskStore.upsert(task)
      toast.add({ title: 'タスクを作成しました', color: 'success' })
      await router.push(`/tasks/${task.id}`)
    } catch (e) { handle(e) }
  }

  async function updateTask(id: number, data: TaskUpdateRequest) {
    try {
      const task = await taskRepository.update(id, data)
      taskStore.upsert(task)
      taskStore.currentTask = { ...taskStore.currentTask!, ...task }
      toast.add({ title: '更新しました', color: 'success' })
    } catch (e) { handle(e) }
  }

  async function deleteTask(id: number) {
    try {
      await taskRepository.remove(id)
      taskStore.remove(id)
      toast.add({ title: '削除しました', color: 'success' })
      await router.push('/')
    } catch (e) { handle(e) }
  }

  async function completeTask(id: number, note?: string) {
    try {
      await taskRepository.complete(id, { note })
      if (taskStore.currentTask?.id === id) {
        taskStore.currentTask = { ...taskStore.currentTask!, status: 'done' }
      }
      toast.add({ title: '完了しました！', color: 'success' })
    } catch (e) { handle(e) }
  }

  async function createChild(parentId: number, data: TaskCreateRequest) {
    try {
      const task = await taskRepository.createChild(parentId, data)
      toast.add({ title: '子タスクを作成しました', color: 'success' })
      return task
    } catch (e) { handle(e) }
  }

  return { fetchTasks, fetchTask, createTask, updateTask, deleteTask, completeTask, createChild }
}
