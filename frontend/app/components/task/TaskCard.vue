<script setup lang="ts">
import type { Task } from '~/types/task'

const { task, selected } = defineProps<{ task: Task, selected?: boolean }>()
const emit = defineEmits<{ select: [task: Task] }>()
</script>

<template>
  <div
    class="flex items-start gap-3 px-2 py-4 border-b border-default cursor-pointer transition-colors hover:bg-elevated/50"
    :class="{ 'bg-primary/10': selected }"
    @click="emit('select', task)"
  >
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-1.5 mb-1.5">
        <TaskTypeBadge :type="task.task_type" />
        <UBadge
          v-if="task.priority === 'must'"
          label="must"
          color="error"
          variant="subtle"
          size="sm"
        />
        <div class="flex-1" />
        <TaskStatusBadge :status="task.status" />
      </div>
      <p class="text-lg font-semibold truncate">
        {{ task.title }}
      </p>
      <div class="flex items-center justify-between mt-1 gap-2">
        <p class="text-sm text-muted truncate">
          {{ task.done_criteria }}
        </p>
        <p
          v-if="task.due_date"
          class="text-sm text-muted shrink-0"
        >
          期限: {{ formatDate(task.due_date) }}
        </p>
      </div>
    </div>
    <UIcon
      name="i-lucide-chevron-right"
      class="text-muted mt-1 shrink-0"
    />
  </div>
</template>
