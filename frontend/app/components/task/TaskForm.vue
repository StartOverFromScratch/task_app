<script setup lang="ts">
import type { TaskCreateRequest } from '~/types/task'

const props = defineProps<{
  initialData?: Partial<TaskCreateRequest>
  submitLabel?: string
}>()

const emit = defineEmits<{
  submit: [data: TaskCreateRequest]
  cancel: []
}>()

const form = reactive<TaskCreateRequest>({
  title: props.initialData?.title ?? '',
  task_type: props.initialData?.task_type ?? 'execution',
  priority: props.initialData?.priority ?? 'must',
  done_criteria: props.initialData?.done_criteria ?? '',
  category: props.initialData?.category ?? null,
  due_date: props.initialData?.due_date ?? null,
  parent_id: props.initialData?.parent_id ?? null,
  reversible: props.initialData?.reversible ?? null,
  exploration_limit: props.initialData?.exploration_limit ?? null,
  decision_criteria: props.initialData?.decision_criteria ?? null
})

const taskTypeItems = [
  { label: 'execution（実行）', value: 'execution' },
  { label: 'research（調査）', value: 'research' },
  { label: 'decision（決定）', value: 'decision' }
]

const priorityItems = [
  { label: 'must（必須）', value: 'must' },
  { label: 'should（推奨）', value: 'should' }
]

const isResearch = computed(() => form.task_type === 'research')

const reversibleChecked = computed({
  get: () => form.reversible === true,
  set: (v: boolean) => { form.reversible = v ? true : null }
})

function handleSubmit() {
  if (!form.title.trim() || !form.done_criteria.trim()) return
  emit('submit', { ...form })
}
</script>

<template>
  <form
    class="space-y-4"
    @submit.prevent="handleSubmit"
  >
    <UFormField
      label="タイトル"
      required
    >
      <UInput
        v-model="form.title"
        placeholder="タスクのタイトル"
        class="w-full"
      />
    </UFormField>

    <div class="grid grid-cols-2 gap-4">
      <UFormField
        label="タイプ"
        required
      >
        <USelect
          v-model="form.task_type"
          :items="taskTypeItems"
          value-key="value"
          class="w-full"
        />
      </UFormField>
      <UFormField
        label="優先度"
        required
      >
        <USelect
          v-model="form.priority"
          :items="priorityItems"
          value-key="value"
          class="w-full"
        />
      </UFormField>
    </div>

    <UFormField
      label="完了条件（Definition of Done）"
      required
    >
      <UTextarea
        v-model="form.done_criteria"
        placeholder="○○の状態になったら完了"
        :rows="2"
        class="w-full"
      />
    </UFormField>

    <div class="grid grid-cols-2 gap-4">
      <UFormField label="カテゴリ">
        <UInput
          :model-value="form.category ?? ''"
          placeholder="任意"
          class="w-full"
          @update:model-value="form.category = $event || null"
        />
      </UFormField>
      <UFormField label="期限">
        <UInput
          :model-value="form.due_date ?? ''"
          type="date"
          class="w-full"
          @update:model-value="form.due_date = $event || null"
        />
      </UFormField>
    </div>

    <UFormField label="可逆判定">
      <UCheckbox
        v-model="reversibleChecked"
        label="可逆（仮決定でOK）"
      />
    </UFormField>

    <template v-if="isResearch">
      <USeparator label="research 設定" />
      <div class="grid grid-cols-2 gap-4">
        <UFormField label="探索上限（件）">
          <UInput
            :model-value="form.exploration_limit !== null && form.exploration_limit !== undefined ? String(form.exploration_limit) : ''"
            type="number"
            placeholder="例: 3"
            class="w-full"
            @update:model-value="form.exploration_limit = $event ? Number($event) : null"
          />
        </UFormField>
        <UFormField label="決定基準">
          <UInput
            :model-value="form.decision_criteria ?? ''"
            placeholder="○○であれば採用"
            class="w-full"
            @update:model-value="form.decision_criteria = $event || null"
          />
        </UFormField>
      </div>
    </template>

    <div class="flex justify-end gap-2 pt-2">
      <UButton
        variant="ghost"
        color="neutral"
        type="button"
        @click="emit('cancel')"
      >
        キャンセル
      </UButton>
      <UButton
        type="submit"
        :disabled="!form.title.trim() || !form.done_criteria.trim()"
      >
        {{ submitLabel ?? '作成する' }}
      </UButton>
    </div>
  </form>
</template>
