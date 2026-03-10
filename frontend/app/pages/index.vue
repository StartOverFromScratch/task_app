<script setup lang="ts">
import type { Task, TaskStatus, TaskType, Priority } from '~/types/task'

const { fetchTasks, fetchTask } = useTask()
const { fetchCandidates } = useCarryover()
const taskStore = useTaskStore()
const carryoverStore = useCarryoverStore()
const router = useRouter()
const { isActive: wakeLockActive, isSupported: wakeLockSupported, toggle: toggleWakeLock } = useWakeLock()

const ALL_STATUSES: TaskStatus[] = ['todo', 'doing', 'done', 'carryover_candidate', 'needs_redefine', 'snoozed']
const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: '未着手',
  doing: '進行中',
  done: '完了',
  carryover_candidate: '繰越候補',
  needs_redefine: '要再定義',
  snoozed: '保留'
}

const selectedStatuses = ref<TaskStatus[]>(['todo', 'doing'])
const typeFilter = ref<TaskType | undefined>(undefined)
const priorityFilter = ref<Priority | undefined>(undefined)
const dueDateFilter = ref<'today_tomorrow' | 'all'>('today_tomorrow')

const staleCount = ref(0)
const carryoverCount = computed(() => carryoverStore.candidates.length)

function toggleStatus(s: TaskStatus) {
  if (selectedStatuses.value.includes(s)) {
    selectedStatuses.value = selectedStatuses.value.filter(x => x !== s)
  } else {
    selectedStatuses.value = [...selectedStatuses.value, s]
  }
  loadTasks()
}

async function loadTasks() {
  await fetchTasks({
    status: selectedStatuses.value.length > 0 ? selectedStatuses.value : undefined,
    sort_by: 'due_date',
    order: 'asc'
  })
}

const filteredTasks = computed(() => {
  let list = taskStore.tasks
  if (typeFilter.value) list = list.filter(t => t.task_type === typeFilter.value)
  if (priorityFilter.value) list = list.filter(t => t.priority === priorityFilter.value)
  if (dueDateFilter.value !== 'all') {
    const today = new Date()
    today.setHours(23, 59, 59, 999)
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    const baseTasks = list.filter(t => t.due_date != null && new Date(t.due_date) <= tomorrow)

    if (baseTasks.length <= 3) {
      const nextDate = list
        .filter(t => t.due_date != null && new Date(t.due_date) > tomorrow)
        .map(t => t.due_date!)
        .sort()[0]

      if (nextDate) {
        const limit = new Date(nextDate)
        limit.setHours(23, 59, 59, 999)
        list = list.filter(t => t.due_date != null && new Date(t.due_date) <= limit)
      } else {
        list = baseTasks
      }
    } else {
      list = baseTasks
    }
  }
  return list
})

function isLargeScreen(): boolean {
  return typeof window !== 'undefined' && window.innerWidth >= 1024
}

async function handleTaskSelect(task: Task) {
  if (isLargeScreen()) {
    taskStore.selectTask(task.id)
    await fetchTask(task.id)
  } else {
    await router.push(`/tasks/${task.id}`)
  }
}

async function handleDetailRefresh() {
  if (taskStore.selectedTaskId) {
    await fetchTask(taskStore.selectedTaskId)
  }
  await loadTasks()
}

onMounted(async () => {
  await loadTasks()
  await fetchCandidates()
  try {
    const stale = await taskRepository.fetchStale()
    staleCount.value = stale.length
  } catch { /* 取得失敗時はカウント0のまま */ }
})
</script>

<template>
  <div class="lg:flex lg:h-[calc(100vh-4rem)] lg:overflow-hidden">
    <!-- 左カラム（全幅 or 360px固定） -->
    <div class="lg:w-[360px] lg:shrink-0 lg:overflow-y-auto lg:border-r border-default p-1">
      <div class="flex items-center justify-between mb-6 space-y-1">
        <h1 class="text-2xl font-bold">
          タスク一覧
        </h1>
        <div class="flex items-center gap-2">
          <UButton
            v-if="wakeLockSupported"
            :icon="wakeLockActive ? 'i-lucide-sun' : 'i-lucide-moon'"
            size="sm"
            :variant="wakeLockActive ? 'solid' : 'ghost'"
            :color="wakeLockActive ? 'warning' : 'neutral'"
            :title="wakeLockActive ? 'スリープ防止中' : 'スリープ防止OFF'"
            @click="toggleWakeLock"
          />
          <UButton
            to="/tasks/new"
            icon="i-lucide-plus"
            size="sm"
          >
            新規作成
          </UButton>
        </div>
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

      <!-- ステータスフィルタ（複数選択） -->
      <div class="flex flex-wrap gap-1 mb-2">
        <UButton
          v-for="s in ALL_STATUSES"
          :key="s"
          size="xs"
          :variant="selectedStatuses.includes(s) ? 'solid' : 'ghost'"
          color="neutral"
          @click="toggleStatus(s)"
        >
          {{ STATUS_LABELS[s] }}
        </UButton>
      </div>

      <!-- 期限フィルタ -->
      <div class="flex flex-wrap gap-1 mb-2">
        <UButton
          v-for="opt in [{ label: '今日・明日', value: 'today_tomorrow' }, { label: '全て', value: 'all' }]"
          :key="opt.value"
          size="xs"
          :variant="dueDateFilter === opt.value ? 'solid' : 'ghost'"
          color="neutral"
          @click="dueDateFilter = opt.value as 'today_tomorrow' | 'all'"
        >
          {{ opt.label }}
        </UButton>
      </div>

      <!-- タイプ・優先度フィルタ -->
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <USelect
          v-model="typeFilter"
          :items="[{ label: 'research', value: 'research' }, { label: 'decision', value: 'decision' }, { label: 'execution', value: 'execution' }]"
          placeholder="全タイプ"
          value-key="value"
          size="sm"
          class="w-32"
        />
        <USelect
          v-model="priorityFilter"
          :items="[{ label: 'must', value: 'must' }, { label: 'should', value: 'should' }]"
          placeholder="全優先度"
          value-key="value"
          size="sm"
          class="w-28"
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
          :selected="task.id === taskStore.selectedTaskId"
          @select="handleTaskSelect"
        />
      </div>
    </div>

    <!-- 右カラム（lgのみ表示） -->
    <div class="hidden lg:flex lg:flex-1 lg:overflow-y-auto p-4">
      <TaskDetailPanel
        v-if="taskStore.currentTask && taskStore.selectedTaskId"
        :task="taskStore.currentTask"
        :task-id="taskStore.selectedTaskId"
        class="w-full"
        @refresh="handleDetailRefresh"
      />
      <div
        v-else
        class="flex flex-1 items-center justify-center text-muted"
      >
        タスクを選択してください
      </div>
    </div>
  </div>
</template>
