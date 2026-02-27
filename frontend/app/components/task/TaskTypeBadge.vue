<script setup lang="ts">
import type { TaskType } from '~/types/task'

const { type } = defineProps<{ type: TaskType }>()

const config: Record<TaskType, { label: string, color: 'primary' | 'warning' | 'success' }> = {
  research: { label: 'research', color: 'primary' },
  decision: { label: 'decision', color: 'warning' },
  execution: { label: 'execution', color: 'success' }
}
</script>

<template>
  <UBadge
    :label="config[type].label"
    :color="config[type].color"
    variant="outline"
    size="sm"
  />
</template>
