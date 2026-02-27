<script setup lang="ts">
import type { TaskCreateRequest } from '~/types/task'

const route = useRoute()
const taskId = Number(route.params.id)
const { fetchTask, updateTask } = useTask()
const taskStore = useTaskStore()
const task = computed(() => taskStore.currentTask)

async function handleSubmit(data: TaskCreateRequest) {
  await updateTask(taskId, data)
  await navigateTo(`/tasks/${taskId}`)
}

onMounted(() => fetchTask(taskId))
</script>

<template>
  <div class="max-w-xl">
    <PageHeader
      title="タスクを編集"
      :back-to="`/tasks/${taskId}`"
    />
    <UCard v-if="task">
      <TaskForm
        :initial-data="task"
        submit-label="更新する"
        @submit="handleSubmit"
        @cancel="navigateTo(`/tasks/${taskId}`)"
      />
    </UCard>
    <div
      v-else
      class="text-center py-12 text-muted"
    >
      読み込み中...
    </div>
  </div>
</template>
