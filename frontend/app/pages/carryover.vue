<script setup lang="ts">
const { fetchCandidates } = useCarryover()
const carryoverStore = useCarryoverStore()

onMounted(fetchCandidates)
</script>

<template>
  <div>
    <PageHeader
      title="繰り越し候補"
      back-to="/"
    />

    <div
      v-if="carryoverStore.candidates.length === 0"
      class="text-center text-muted py-12"
    >
      繰り越し候補のタスクはありません
    </div>
    <div
      v-else
      class="space-y-4"
    >
      <CarryoverActionBar
        v-for="task in carryoverStore.candidates"
        :key="task.id"
        :task="task"
        @done="fetchCandidates"
      />
    </div>
  </div>
</template>
