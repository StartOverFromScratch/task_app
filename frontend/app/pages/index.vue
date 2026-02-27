<script setup lang="ts">
import type { TaskStatus, TaskType, Priority } from '~/types/task'

const { fetchTasks } = useTask()
const { fetchCandidates } = useCarryover()
const taskStore = useTaskStore()
const carryoverStore = useCarryoverStore()

const statusFilter = ref<TaskStatus | undefined>(undefined)
const typeFilter = ref<TaskType | undefined>(undefined)
const priorityFilter = ref<Priority | undefined>(undefined)

const statusTabs: Array<{ label: string, value: TaskStatus | undefined }> = [
  { label: '全て', value: undefined },
  { label: '未着手', value: 'todo' },
  { label: '進行中', value: 'doing' },
  { label: '完了', value: 'done' }
]

const filteredTasks = computed(() => {
  let list = taskStore.tasks.filter(t => !t.parent_id)
  if (statusFilter.value) list = list.filter(t => t.status === statusFilter.value)
  if (typeFilter.value) list = list.filter(t => t.task_type === typeFilter.value)
  if (priorityFilter.value) list = list.filter(t => t.priority === priorityFilter.value)
  return list
})

const staleCount = ref(0)
const carryoverCount = computed(() => carryoverStore.candidates.length)

onMounted(async () => {
  await fetchTasks()
  await fetchCandidates()
  try {
    const stale = await taskRepository.fetchStale()
    staleCount.value = stale.length
  } catch { /* 取得失敗時はカウント0のまま */ }
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">
        タスク一覧
      </h1>
      <UButton
        to="/tasks/new"
        icon="i-lucide-plus"
      >
        新規作成
      </UButton>
    </div>

    <div class="flex flex-wrap gap-2 mb-4">
      <UAlert
        v-if="staleCount > 0"
        :title="`放置タスク ${staleCount}件`"
        color="warning"
        variant="subtle"
        icon="i-lucide-clock"
        :actions="[{ label: '確認する', to: '/stale', variant: 'outline', size: 'xs' }]"
        class="flex-1"
      />
      <UAlert
        v-if="carryoverCount > 0"
        :title="`繰り越し候補 ${carryoverCount}件`"
        color="error"
        variant="subtle"
        icon="i-lucide-calendar-x"
        :actions="[{ label: '処理する', to: '/carryover', variant: 'outline', size: 'xs' }]"
        class="flex-1"
      />
    </div>

    <div class="flex flex-wrap items-center gap-2 mb-4">
      <div class="flex gap-1">
        <UButton
          v-for="tab in statusTabs"
          :key="tab.label"
          size="sm"
          :variant="statusFilter === tab.value ? 'solid' : 'ghost'"
          color="neutral"
          @click="statusFilter = tab.value"
        >
          {{ tab.label }}
        </UButton>
      </div>
      <USelect
        v-model="typeFilter"
        :items="[{ label: 'research', value: 'research' }, { label: 'decision', value: 'decision' }, { label: 'execution', value: 'execution' }]"
        placeholder="全タイプ"
        value-key="value"
        size="sm"
        class="w-36"
      />
      <USelect
        v-model="priorityFilter"
        :items="[{ label: 'must', value: 'must' }, { label: 'should', value: 'should' }]"
        placeholder="全優先度"
        value-key="value"
        size="sm"
        class="w-32"
      />
    </div>

    <div
      v-if="filteredTasks.length === 0"
      class="text-center text-muted py-12"
    >
      タスクがありません
    </div>
    <div
      v-else
      class="space-y-2"
    >
      <TaskCard
        v-for="task in filteredTasks"
        :key="task.id"
        :task="task"
      />
    </div>
  </div>
</template>
