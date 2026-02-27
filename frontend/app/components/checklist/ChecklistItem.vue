<script setup lang="ts">
import type { ChecklistItem } from '~/types/checklist'

const props = defineProps<{ taskId: number, item: ChecklistItem }>()
const emit = defineEmits<{ refresh: [] }>()

const { updateItem, extractItem } = useChecklist()

async function toggle() {
  if (props.item.extracted_task_id) return
  await updateItem(props.taskId, props.item.id, { is_done: !props.item.is_done })
  emit('refresh')
}

async function extract() {
  await extractItem(props.taskId, props.item.id)
  emit('refresh')
}
</script>

<template>
  <div class="flex items-center gap-2 py-1.5">
    <UCheckbox
      :model-value="item.is_done"
      :disabled="!!item.extracted_task_id"
      @change="toggle"
    />
    <span
      class="flex-1 text-sm"
      :class="{ 'line-through text-muted': item.is_done }"
    >{{ item.text }}</span>

    <NuxtLink
      v-if="item.extracted_task_id"
      :to="`/tasks/${item.extracted_task_id}`"
      class="text-xs text-primary hover:underline"
    >
      →タスク
    </NuxtLink>
    <UButton
      v-else
      size="xs"
      variant="ghost"
      color="neutral"
      icon="i-lucide-arrow-up-right"
      title="タスクとして切り出し"
      @click="extract"
    />
  </div>
</template>
