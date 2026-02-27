<script setup lang="ts">
import type { CarryoverCandidate } from '~/types/carryover'

const props = defineProps<{ task: CarryoverCandidate }>()
const emit = defineEmits<{ done: [] }>()

const { doCarryover } = useCarryover()
const loading = ref<string | null>(null)

async function act(action: 'today' | 'plus_2d' | 'plus_7d' | 'needs_redefine') {
  loading.value = action
  await doCarryover(props.task.id, action)
  loading.value = null
  emit('done')
}
</script>

<template>
  <UCard>
    <div class="space-y-3">
      <div class="flex flex-wrap items-center gap-2">
        <TaskTypeBadge :type="task.task_type" />
        <UBadge
          v-if="task.priority === 'must'"
          label="must"
          color="error"
          variant="subtle"
          size="sm"
        />
        <span class="text-sm text-error font-medium">{{ task.overdue_days }}日超過</span>
      </div>
      <p class="font-medium">
        {{ task.title }}
      </p>
      <p class="text-sm text-muted">
        完了条件: {{ task.done_criteria }}
      </p>
      <p
        v-if="task.due_date"
        class="text-xs text-muted"
      >
        元の期限: {{ formatDate(task.due_date) }}
      </p>
      <div class="flex flex-wrap gap-2 pt-1">
        <UButton
          size="sm"
          :loading="loading === 'today'"
          @click="act('today')"
        >
          今日やる
        </UButton>
        <UButton
          size="sm"
          variant="outline"
          :loading="loading === 'plus_2d'"
          @click="act('plus_2d')"
        >
          +2日
        </UButton>
        <UButton
          size="sm"
          variant="outline"
          :loading="loading === 'plus_7d'"
          @click="act('plus_7d')"
        >
          +7日
        </UButton>
        <UButton
          size="sm"
          variant="ghost"
          color="error"
          :loading="loading === 'needs_redefine'"
          @click="act('needs_redefine')"
        >
          要再定義
        </UButton>
      </div>
    </div>
  </UCard>
</template>
