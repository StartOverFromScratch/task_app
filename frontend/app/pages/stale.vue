<script setup lang="ts">
const { mustTasks, shouldTasks, fetchStale } = useStale()

onMounted(() => fetchStale())
</script>

<template>
  <div>
    <PageHeader
      title="放置タスク"
      back-to="/"
    />

    <div
      v-if="mustTasks.length === 0 && shouldTasks.length === 0"
      class="text-center text-muted py-12"
    >
      放置タスクはありません
    </div>

    <div
      v-if="mustTasks.length > 0"
      class="mb-8"
    >
      <h2 class="text-lg font-semibold mb-3 text-error">
        must（7日以上更新なし）
      </h2>
      <div class="space-y-2">
        <UCard
          v-for="task in mustTasks"
          :key="task.id"
          class="flex items-center justify-between"
        >
          <div class="flex-1 min-w-0">
            <p class="font-medium truncate">
              {{ task.title }}
            </p>
            <p class="text-sm text-muted">
              最終更新: {{ task.stale_days }}日前
            </p>
          </div>
          <UButton
            :to="`/tasks/${task.id}`"
            variant="outline"
            size="sm"
            icon="i-lucide-arrow-right"
          >
            向き合う
          </UButton>
        </UCard>
      </div>
    </div>

    <div v-if="shouldTasks.length > 0">
      <h2 class="text-lg font-semibold mb-3 text-warning">
        should（21日以上更新なし）
      </h2>
      <div class="space-y-2">
        <UCard
          v-for="task in shouldTasks"
          :key="task.id"
          class="flex items-center justify-between"
        >
          <div class="flex-1 min-w-0">
            <p class="font-medium truncate">
              {{ task.title }}
            </p>
            <p class="text-sm text-muted">
              最終更新: {{ task.stale_days }}日前
            </p>
          </div>
          <UButton
            :to="`/tasks/${task.id}`"
            variant="outline"
            size="sm"
            icon="i-lucide-arrow-right"
          >
            向き合う
          </UButton>
        </UCard>
      </div>
    </div>
  </div>
</template>
