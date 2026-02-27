import type { StaleTask } from '~/types/carryover'

export function useStale() {
  const staleTasks = ref<StaleTask[]>([])
  const { handle } = useErrorToast()

  async function fetchStale(priority?: 'must' | 'should') {
    try {
      staleTasks.value = await taskRepository.fetchStale(priority)
    } catch (e) { handle(e) }
  }

  const mustTasks = computed(() => staleTasks.value.filter(t => t.priority === 'must'))
  const shouldTasks = computed(() => staleTasks.value.filter(t => t.priority === 'should'))

  return { staleTasks, mustTasks, shouldTasks, fetchStale }
}
