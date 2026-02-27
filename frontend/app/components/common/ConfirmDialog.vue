<script setup lang="ts">
const { title, description } = defineProps<{
  title?: string
  description?: string
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <div class="p-4 space-y-4">
    <p class="font-semibold">
      {{ title ?? '確認' }}
    </p>
    <p
      v-if="description"
      class="text-sm text-muted"
    >
      {{ description }}
    </p>
    <div class="flex justify-end gap-2">
      <UButton
        variant="ghost"
        color="neutral"
        @click="emit('cancel')"
      >
        キャンセル
      </UButton>
      <UButton
        color="error"
        @click="emit('confirm')"
      >
        削除する
      </UButton>
    </div>
  </div>
</template>
