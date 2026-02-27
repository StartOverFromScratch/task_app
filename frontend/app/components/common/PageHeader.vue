<script setup lang="ts">
defineProps<{
  title: string
  backTo?: string
}>()
</script>

<template>
  <div class="mb-6">
    <UButton
      v-if="backTo"
      :to="backTo"
      variant="ghost"
      color="neutral"
      icon="i-lucide-arrow-left"
      class="mb-2"
    >
      戻る
    </UButton>
    <h1 class="text-2xl font-bold">
      {{ title }}
    </h1>
  </div>
</template>
