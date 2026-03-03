<script setup lang="ts">
import type { ChecklistItem } from '~/types/checklist'

const props = defineProps<{ taskId: number, item: ChecklistItem }>()
const emit = defineEmits<{ refresh: [] }>()

const { updateItem, extractItem } = useChecklist()

const editing = ref(false)
const editText = ref('')

async function toggle() {
  if (props.item.extracted_task_id) return
  await updateItem(props.taskId, props.item.id, { is_done: !props.item.is_done })
  emit('refresh')
}

async function extract() {
  await extractItem(props.taskId, props.item.id)
  emit('refresh')
}

function startEdit() {
  if (props.item.extracted_task_id) return
  editText.value = props.item.text
  editing.value = true
}

async function commitEdit(e?: KeyboardEvent) {
  if (e?.isComposing) return
  const trimmed = editText.value.trim()
  editing.value = false
  if (!trimmed || trimmed === props.item.text) return
  await updateItem(props.taskId, props.item.id, { text: trimmed })
  emit('refresh')
}

function cancelEdit() {
  editing.value = false
}
</script>

<template>
  <div class="flex items-center gap-2 py-1.5">
    <UCheckbox
      :model-value="item.is_done"
      :disabled="!!item.extracted_task_id"
      @change="toggle"
    />

    <UInput
      v-if="editing"
      v-model="editText"
      size="sm"
      class="flex-1"
      autofocus
      @keydown.enter.prevent="commitEdit"
      @keydown.esc.prevent="cancelEdit"
      @blur="commitEdit"
    />
    <span
      v-else
      class="flex-1 text-sm"
      :class="{ 'line-through text-muted': item.is_done, 'cursor-pointer hover:text-primary': !item.extracted_task_id }"
      @dblclick="startEdit"
    >{{ item.text }}</span>

    <template v-if="!editing">
      <UButton
        v-if="!item.extracted_task_id"
        size="xs"
        variant="ghost"
        color="neutral"
        icon="i-lucide-pencil"
        title="テキストを編集"
        @click="startEdit"
      />
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
    </template>
  </div>
</template>
