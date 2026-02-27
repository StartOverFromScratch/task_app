<script setup lang="ts">
import type { ChecklistItem } from '~/types/checklist'

const props = defineProps<{ taskId: number, items: ChecklistItem[] }>()
const emit = defineEmits<{ refresh: [] }>()

const { createItem } = useChecklist()
const newText = ref('')

async function handleAdd() {
  if (!newText.value.trim()) return
  await createItem(props.taskId, { text: newText.value.trim() })
  newText.value = ''
  emit('refresh')
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold">
        チェックリスト
      </h3>
    </div>

    <div class="divide-y divide-muted">
      <ChecklistItem
        v-for="item in items"
        :key="item.id"
        :task-id="taskId"
        :item="item"
        @refresh="emit('refresh')"
      />
    </div>

    <div class="flex gap-2 mt-3">
      <UInput
        v-model="newText"
        placeholder="新しいアイテムを追加..."
        size="sm"
        class="flex-1"
        @keydown.enter.prevent="handleAdd"
      />
      <UButton
        size="sm"
        icon="i-lucide-plus"
        :disabled="!newText.trim()"
        @click="handleAdd"
      />
    </div>
  </div>
</template>
