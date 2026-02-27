import { defineStore } from 'pinia'
import type { Task, TaskDetail } from '~/types/task'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<TaskDetail | null>(null)

  function upsert(task: Task) {
    const idx = tasks.value.findIndex(t => t.id === task.id)
    if (idx >= 0) tasks.value[idx] = task
    else tasks.value.unshift(task)
  }

  function remove(id: number) {
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  function setAll(list: Task[]) {
    tasks.value = list
  }

  return { tasks, currentTask, upsert, remove, setAll }
})
