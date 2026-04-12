<script setup lang="ts">
import type { Task } from '~/types/task'
import type { NavItem } from '~/composables/useNavItems'

const { fetchTasks, fetchTask } = useTask()
const { fetchCandidates } = useCarryover()
const taskStore = useTaskStore()
const carryoverStore = useCarryoverStore()
const router = useRouter()
const route = useRoute()
const { NAV_ITEMS } = useNavItems()

// ナビ選択状態
const selectedNavKey = ref<string>('today')

// モバイル表示状態（'nav' = ナビのみ, 'list' = リスト表示）
const mobileView = ref<'nav' | 'list'>('nav')

// 放置タスク件数
const staleCount = ref(0)
const carryoverCount = computed(() => carryoverStore.candidates.length)

function isLargeScreen(): boolean {
  return typeof window !== 'undefined' && window.innerWidth >= 1024
}

// 現在のナビキーに応じたフィルタパラメータを返す
function getParams(navKey: string) {
  const item = NAV_ITEMS.find(n => n.key === navKey)
  if (!item || !item.filter) return { sort_by: 'due_date' as const, order: 'asc' as const }
  return {
    status: item.filter.statuses,
    sort_by: 'due_date' as const,
    order: 'asc' as const
  }
}

async function loadTasks(navKey?: string) {
  await fetchTasks(getParams(navKey ?? selectedNavKey.value))
}

// 今日・明日フィルタ + 自動拡張ロジック
const filteredTasks = computed(() => {
  const item = NAV_ITEMS.find(n => n.key === selectedNavKey.value)
  if (!item?.filter?.dueDateLimit) return taskStore.tasks

  const list = taskStore.tasks
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
      return list.filter(t => t.due_date != null && new Date(t.due_date) <= limit)
    }
    return baseTasks
  }
  return baseTasks
})

// 現在選択中ナビのラベル
const selectedNavLabel = computed(() => {
  return NAV_ITEMS.find(n => n.key === selectedNavKey.value)?.label ?? ''
})

async function handleNavSelect(item: NavItem) {
  if (item.to) {
    router.push(item.to)
    return
  }
  selectedNavKey.value = item.key
  taskStore.selectTask(null)
  if (!isLargeScreen()) {
    mobileView.value = 'list'
  }
  await loadTasks(item.key)
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

function handleBack() {
  mobileView.value = 'nav'
  taskStore.selectTask(null)
}

onMounted(async () => {
  if (route.query.view === 'list') {
    mobileView.value = 'list'
  }
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
    <!-- 左カラム: AppNav（PC常時表示 / モバイルはnavモード時のみ） -->
    <div
      class="lg:w-[240px] lg:shrink-0 lg:overflow-y-auto lg:border-r border-default"
      :class="{ 'hidden lg:block': mobileView === 'list' }"
    >
      <!-- AppNav ナビゲーション -->
      <AppNav
        :model-value="selectedNavKey"
        :stale-count="staleCount"
        :carryover-count="carryoverCount"
        @update:model-value="selectedNavKey = $event"
        @navigate="handleNavSelect"
      />

      <!-- 新規作成ボタン（モバイルのナビ画面） -->
      <div class="px-4 pt-2 lg:hidden">
        <UButton
          to="/tasks/new"
          icon="i-lucide-plus"
          size="sm"
          block
        >
          新規作成
        </UButton>
      </div>

      <!-- 設定ボタン（モバイルのナビ画面） -->
      <div class="px-4 pt-10 ">
        <UButton
          to="/settings"
          icon="i-lucide-settings"
          size="sm"
          variant="ghost"
          color="neutral"
          title="設定"
          block
        >
          設定
        </UButton>
      </div>
    </div>

    <!-- 右カラム: タスクリスト + 詳細パネル（PC常時表示 / モバイルはlistモード時のみ） -->
    <div
      class="lg:flex lg:flex-1 lg:overflow-hidden"
      :class="{ 'hidden lg:flex': mobileView === 'nav' }"
    >
      <!-- タスクリスト -->
      <div class="flex-1 overflow-y-auto p-4 lg:max-w-[360px] lg:border-r border-default">
        <!-- リストヘッダー -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-arrow-left"
              size="sm"
              variant="ghost"
              color="neutral"
              class="lg:hidden"
              @click="handleBack"
            />
            <h2 class="text-2xl font-semibold">
              {{ selectedNavLabel }}
            </h2>
          </div>
          <UButton
            to="/tasks/new"
            icon="i-lucide-plus"
            size="sm"
          >
            新規作成
          </UButton>
        </div>

        <!-- タスクリスト本体 -->
        <div
          v-if="filteredTasks.length === 0"
          class="text-center text-muted py-12"
        >
          タスクがありません
        </div>
        <div
          v-else
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

      <!-- 詳細パネル（lgのみ） -->
      <div class="hidden lg:flex lg:flex-1 lg:overflow-y-auto p-4">
        <TaskDetailPanel
          v-if="taskStore.currentTask && taskStore.selectedTaskId"
          :task="taskStore.currentTask"
          :task-id="taskStore.selectedTaskId"
          class="w-full"
          @refresh="handleDetailRefresh"
          @back="handleBack"
        />
        <div
          v-else
          class="flex flex-1 items-center justify-center text-muted"
        >
          タスクを選択してください
        </div>
      </div>
    </div>
  </div>
</template>
