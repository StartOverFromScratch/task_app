<script setup lang="ts">
import type { TaskCreateRequest } from '~/types/task'

const { createTask } = useTask()

async function handleSubmit(data: TaskCreateRequest) {
  await createTask(data)
}
</script>

<template>
  <div class="max-w-xl">
    <PageHeader
      title="タスクを作成"
      back-to="/"
    />
    <UCard>
      <TaskForm
        @submit="handleSubmit"
        @cancel="navigateTo('/')"
      />
    </UCard>
  </div>
</template>
