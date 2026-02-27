<script setup lang="ts">
const route = useRoute()
const taskId = Number(route.params.id)

const { fetchTask, updateTask, deleteTask, completeTask } = useTask()
const taskStore = useTaskStore()
const task = computed(() => taskStore.currentTask)

const showDeleteModal = ref(false)
const showCompleteModal = ref(false)
const completeNote = ref('')

async function handleRefresh() {
  await fetchTask(taskId)
}

async function handleComplete() {
  await completeTask(taskId, completeNote.value || undefined)
  showCompleteModal.value = false
  await handleRefresh()
}

async function handleDelete() {
  await deleteTask(taskId)
}

async function handleStatusChange(status: string) {
  await updateTask(taskId, { status: status as Exclude<import('~/types/task').TaskStatus, 'done'> })
  await handleRefresh()
}

onMounted(() => fetchTask(taskId))
</script>

<template>
  <div v-if="task">
    <PageHeader
      :title="task.title"
      back-to="/"
    />

    <div class="grid gap-6 lg:grid-cols-3">
      <div class="lg:col-span-2 space-y-4">
        <!-- メタ情報 -->
        <UCard>
          <div class="space-y-3">
            <div class="flex flex-wrap gap-2 items-center">
              <TaskTypeBadge :type="task.task_type" />
              <TaskStatusBadge :status="task.status" />
              <UBadge
                :label="task.priority"
                :color="task.priority === 'must' ? 'error' : 'neutral'"
                variant="subtle"
                size="sm"
              />
              <span
                v-if="task.due_date"
                class="text-sm text-muted"
              >期限: {{ formatDate(task.due_date) }}</span>
            </div>

            <div>
              <p class="text-xs text-muted font-medium mb-1">
                完了条件
              </p>
              <p class="text-sm">
                {{ task.done_criteria }}
              </p>
            </div>

            <div v-if="task.decision_criteria">
              <p class="text-xs text-muted font-medium mb-1">
                決定基準
              </p>
              <p class="text-sm">
                {{ task.decision_criteria }}
              </p>
            </div>

            <div
              v-if="task.exploration_limit !== null"
              class="flex gap-4 text-sm"
            >
              <span>探索上限: {{ task.exploration_limit }}件</span>
              <span v-if="task.reversible !== null">可逆: {{ task.reversible ? 'はい' : 'いいえ' }}</span>
            </div>

            <div
              v-if="task.origin"
              class="text-sm text-muted border-l-2 border-muted pl-3"
            >
              <NuxtLink
                :to="`/tasks/${task.origin.parent_task_id}`"
                class="hover:underline"
              >
                「{{ task.origin.parent_task_title }}」の「{{ task.origin.checklist_item_text }}」から切り出し
              </NuxtLink>
            </div>
          </div>

          <template #footer>
            <div class="flex flex-wrap gap-2">
              <UButton
                v-if="task.status !== 'done'"
                icon="i-lucide-check-circle"
                color="success"
                @click="showCompleteModal = true"
              >
                完了にする
              </UButton>
              <UButton
                variant="outline"
                :to="`/tasks/${task.id}/edit`"
                icon="i-lucide-pencil"
              >
                編集
              </UButton>
              <UButton
                variant="ghost"
                color="error"
                icon="i-lucide-trash-2"
                @click="showDeleteModal = true"
              >
                削除
              </UButton>
            </div>
          </template>
        </UCard>

        <!-- チェックリスト -->
        <UCard>
          <ChecklistPanel
            :task-id="taskId"
            :items="task.checklist || []"
            @refresh="handleRefresh"
          />
        </UCard>

        <!-- 子タスク -->
        <UCard>
          <TaskChildList
            :parent-id="taskId"
            :children="task.children || []"
            @refresh="handleRefresh"
          />
        </UCard>
      </div>

      <!-- サイドバー -->
      <div class="space-y-4">
        <UCard>
          <div class="space-y-2">
            <p class="text-sm font-medium text-muted">
              ステータス変更
            </p>
            <div class="space-y-1">
              <UButton
                v-for="s in ['todo', 'doing', 'needs_redefine', 'snoozed']"
                :key="s"
                size="sm"
                block
                :variant="task.status === s ? 'solid' : 'ghost'"
                color="neutral"
                @click="handleStatusChange(s)"
              >
                {{ { todo: '未着手', doing: '進行中', needs_redefine: '要再定義', snoozed: '保留' }[s] }}
              </UButton>
            </div>
          </div>
        </UCard>
        <UCard>
          <p class="text-xs text-muted">
            最終更新: {{ formatDateTime(task.last_updated_at) }}
          </p>
          <p class="text-xs text-muted mt-1">
            作成: {{ formatDateTime(task.created_at) }}
          </p>
        </UCard>
      </div>
    </div>

    <!-- 完了モーダル -->
    <UModal
      v-model:open="showCompleteModal"
      title="タスクを完了する"
    >
      <template #body>
        <div class="space-y-3">
          <p class="text-sm">
            完了条件を満たしましたか？
          </p>
          <p class="text-sm font-medium">
            {{ task.done_criteria }}
          </p>
          <UFormField label="完了メモ（任意）">
            <UTextarea
              v-model="completeNote"
              placeholder="完了時のメモ"
              :rows="2"
              class="w-full"
            />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            variant="ghost"
            color="neutral"
            @click="showCompleteModal = false"
          >
            キャンセル
          </UButton>
          <UButton
            color="success"
            @click="handleComplete"
          >
            完了する
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- 削除確認モーダル -->
    <UModal
      v-model:open="showDeleteModal"
      title="タスクを削除"
    >
      <template #body>
        <p class="text-sm">
          「{{ task.title }}」を削除します。この操作は元に戻せません。
        </p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            variant="ghost"
            color="neutral"
            @click="showDeleteModal = false"
          >
            キャンセル
          </UButton>
          <UButton
            color="error"
            @click="handleDelete"
          >
            削除する
          </UButton>
        </div>
      </template>
    </UModal>
  </div>
  <div
    v-else
    class="text-center py-12 text-muted"
  >
    読み込み中...
  </div>
</template>
