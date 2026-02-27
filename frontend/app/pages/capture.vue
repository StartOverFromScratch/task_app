<script setup lang="ts">
const { fetchCaptures, updateCapture, deleteCapture } = useCapture()
const captureStore = useCaptureStore()
const tab = ref<'unresolved' | 'resolved'>('unresolved')

const displayItems = computed(() =>
  tab.value === 'unresolved' ? captureStore.unresolved : captureStore.resolved
)

onMounted(() => fetchCaptures())

async function toggleResolved(id: number, isResolved: boolean) {
  await updateCapture(id, { is_resolved: !isResolved })
}
</script>

<template>
  <div>
    <PageHeader
      title="CaptureBox"
      back-to="/"
    />

    <CaptureInput class="mb-6" />

    <div class="flex gap-2 mb-4">
      <UButton
        size="sm"
        :variant="tab === 'unresolved' ? 'solid' : 'ghost'"
        color="neutral"
        @click="tab = 'unresolved'"
      >
        未解決 ({{ captureStore.unresolved.length }})
      </UButton>
      <UButton
        size="sm"
        :variant="tab === 'resolved' ? 'solid' : 'ghost'"
        color="neutral"
        @click="tab = 'resolved'"
      >
        解決済み ({{ captureStore.resolved.length }})
      </UButton>
    </div>

    <div
      v-if="displayItems.length === 0"
      class="text-center text-muted py-8"
    >
      アイテムなし
    </div>
    <div
      v-else
      class="space-y-2"
    >
      <UCard
        v-for="item in displayItems"
        :key="item.id"
      >
        <div class="flex items-start gap-3">
          <div class="flex-1 min-w-0">
            <p
              class="text-sm"
              :class="{ 'line-through text-muted': item.is_resolved }"
            >
              {{ item.text }}
            </p>
            <div class="flex items-center gap-2 mt-1">
              <p class="text-xs text-muted">
                {{ formatDateTime(item.created_at) }}
              </p>
              <NuxtLink
                v-if="item.related_task_id"
                :to="`/tasks/${item.related_task_id}`"
                class="text-xs text-primary hover:underline"
              >関連タスク</NuxtLink>
            </div>
          </div>
          <div class="flex gap-1">
            <UButton
              size="xs"
              variant="ghost"
              :color="item.is_resolved ? 'neutral' : 'success'"
              :icon="item.is_resolved ? 'i-lucide-undo-2' : 'i-lucide-check'"
              @click="toggleResolved(item.id, item.is_resolved)"
            />
            <UButton
              size="xs"
              variant="ghost"
              color="error"
              icon="i-lucide-trash-2"
              @click="deleteCapture(item.id)"
            />
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
