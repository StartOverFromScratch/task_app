<script setup lang="ts">
import type { TaskStatus } from '~/types/task'

const { status } = defineProps<{ status: TaskStatus }>()

type BadgeColor = 'neutral' | 'info' | 'success' | 'warning' | 'error' | 'primary' | 'secondary'
const config: Record<TaskStatus, { label: string, color: BadgeColor }> = {
  todo: { label: '未着手', color: 'neutral' },
  doing: { label: '進行中', color: 'info' },
  done: { label: '完了', color: 'success' },
  carryover_candidate: { label: '繰り越し候補', color: 'warning' },
  needs_redefine: { label: '要再定義', color: 'error' },
  snoozed: { label: '保留', color: 'secondary' }
}
</script>

<template>
  <UBadge
    :label="config[status].label"
    :color="config[status].color"
    variant="subtle"
    size="sm"
  />
</template>
