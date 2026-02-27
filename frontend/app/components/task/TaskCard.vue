<script setup lang="ts">
import type { Task } from '~/types/task'

const { task } = defineProps<{ task: Task }>()
</script>

<template>
  <NuxtLink :to="`/tasks/${task.id}`">
    <UCard class="hover:bg-elevated/50 transition-colors cursor-pointer">
      <div class="flex items-start gap-3">
        <div class="flex-1 min-w-0">
          <div class="flex flex-wrap items-center gap-1.5 mb-1">
            <TaskTypeBadge :type="task.task_type" />
            <TaskStatusBadge :status="task.status" />
            <UBadge
              v-if="task.priority === 'must'"
              label="must"
              color="error"
              variant="subtle"
              size="sm"
            />
          </div>
          <p class="font-medium">{{ task.title }}</p>
          <p class="text-sm text-muted mt-0.5 truncate">{{ task.done_criteria }}</p>
          <p
            v-if="task.due_date"
            class="text-xs text-muted mt-1"
          >
            期限: {{ formatDate(task.due_date) }}
          </p>
        </div>
        <UIcon
          name="i-lucide-chevron-right"
          class="text-muted mt-1 shrink-0"
        />
      </div>
    </UCard>
  </NuxtLink>
</template>
