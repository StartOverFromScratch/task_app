<script setup lang="ts">
import type { Task, TaskCreateRequest } from '~/types/task'

const props = defineProps<{ parentId: number, children: Task[] }>()
const emit = defineEmits<{ refresh: [] }>()

const { createChild } = useTask()
const showForm = ref(false)

async function handleCreate(data: TaskCreateRequest) {
  await createChild(props.parentId, data)
  showForm.value = false
  emit('refresh')
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold">
        子タスク
      </h3>
      <UButton
        size="sm"
        variant="ghost"
        icon="i-lucide-plus"
        @click="showForm = !showForm"
      >
        追加
      </UButton>
    </div>

    <div
      v-if="showForm"
      class="mb-4 p-4 border border-muted rounded-lg"
    >
      <TaskForm
        submit-label="子タスクを作成"
        @submit="handleCreate"
        @cancel="showForm = false"
      />
    </div>

    <div
      v-if="children.length === 0"
      class="text-sm text-muted py-2"
    >
      子タスクなし
    </div>
    <div
      v-else
      class="space-y-2"
    >
      <NuxtLink
        v-for="child in children"
        :key="child.id"
        :to="`/tasks/${child.id}`"
        class="flex items-center gap-2 p-2 rounded hover:bg-elevated/50 transition-colors"
      >
        <TaskStatusBadge :status="child.status" />
        <span class="text-sm flex-1 truncate">{{ child.title }}</span>
        <UIcon
          name="i-lucide-chevron-right"
          class="text-muted"
        />
      </NuxtLink>
    </div>
  </div>
</template>
