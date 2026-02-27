<script setup lang="ts">
const { createCapture } = useCapture()
const text = ref('')

async function handleAdd() {
  if (!text.value.trim()) return
  await createCapture({ text: text.value.trim() })
  text.value = ''
}
</script>

<template>
  <div class="flex gap-2">
    <UInput
      v-model="text"
      placeholder="分岐論点・メモを入力..."
      class="flex-1"
      @keydown.enter.prevent="handleAdd"
    />
    <UButton
      icon="i-lucide-plus"
      :disabled="!text.trim()"
      @click="handleAdd"
    >
      追加
    </UButton>
  </div>
</template>
