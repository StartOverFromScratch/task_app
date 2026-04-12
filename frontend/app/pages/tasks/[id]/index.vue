<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const taskId = Number(route.params.id)

const { fetchTask } = useTask()
const taskStore = useTaskStore()
const task = computed(() => taskStore.currentTask)

async function handleRefresh() {
  await fetchTask(taskId)
}

onMounted(() => fetchTask(taskId))
</script>

<template>
  <div v-if="task">
    <TaskDetailPanel
      :task="task"
      :task-id="taskId"
      @refresh="handleRefresh"
      @back="router.push('/?view=list')"
    />
  </div>
  <div
    v-else
    class="text-center py-12 text-muted"
  >
    読み込み中...
  </div>
</template>
