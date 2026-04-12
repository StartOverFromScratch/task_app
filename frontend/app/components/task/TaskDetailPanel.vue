<script setup lang="ts">
import type { TaskDetail } from '~/types/task'

const { task, taskId } = defineProps<{ task: TaskDetail, taskId: number }>()
const emit = defineEmits<{ refresh: [], back: [] }>()

const { updateTask, deleteTask, completeTask } = useTask()

const showDeleteModal = ref(false)
const showCompleteModal = ref(false)
const completeNote = ref('')

async function handleComplete() {
  await completeTask(taskId, completeNote.value || undefined)
  showCompleteModal.value = false
  emit('refresh')
}

async function handleDelete() {
  await deleteTask(taskId)
  showDeleteModal.value = false
}

async function handleStatusChange(s: string) {
  await updateTask(taskId, { status: s as Exclude<import('~/types/task').TaskStatus, 'done'> })
  emit('refresh')
}
function handleBack() {
  emit('back')
}
</script>

<template>
  <div class="space-y-4">
    <UButton
      icon="i-lucide-arrow-left"
      size="sm"
      variant="ghost"
      color="neutral"
      class="lg:hidden"
      @click="handleBack"
    />
    <!-- ヘッダー -->
    <div class="flex items-start justify-between gap-2">
      <h2 class="text-xl font-bold leading-tight">
        {{ task.title }}
      </h2>
      <div class="flex gap-1 shrink-0">
        <UButton
          variant="outline"
          size="sm"
          icon="i-lucide-pencil"
          :to="`/tasks/${taskId}/edit`"
        >
          編集
        </UButton>
        <UButton
          variant="ghost"
          color="error"
          size="sm"
          icon="i-lucide-trash-2"
          @click="showDeleteModal = true"
        />
      </div>
    </div>

    <!-- メタ情報 -->
    <UCard>
      <div class="space-y-3">
        <div class="flex flex-wrap gap-2 items-center">
          <TaskTypeBadge :type="task.task_type" />
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
            v-for="s in ['todo', 'doing', 'needs_redefine', 'snoozed']"
            :key="s"
            size="xs"
            :variant="task.status === s ? 'solid' : 'ghost'"
            color="neutral"
            @click="handleStatusChange(s)"
          >
            {{ { todo: '未着手', doing: '進行中', needs_redefine: '要再定義', snoozed: '保留' }[s] }}
          </UButton>
          <UButton
            v-if="task.status !== 'done'"
            icon="i-lucide-check-circle"
            color="success"
            size="sm"
            @click="showCompleteModal = true"
          >
            完了
          </UButton>
        </div>
      </template>
    </UCard>

    <!-- チェックリスト -->
    <UCard>
      <ChecklistPanel
        :task-id="taskId"
        :items="task.checklist || []"
        @refresh="emit('refresh')"
      />
    </UCard>

    <!-- 子タスク -->
    <UCard>
      <TaskChildList
        :parent-id="taskId"
        :children="task.children || []"
        @refresh="emit('refresh')"
      />
    </UCard>

    <!-- タイムスタンプ -->
    <p class="text-xs text-muted">
      最終更新: {{ formatDateTime(task.last_updated_at) }} / 作成: {{ formatDateTime(task.created_at) }}
    </p>

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
</template>
