<script setup lang="ts">
const apiBase = useApiBase()
const toast = useToast()

const notifyTime = ref<string>('')
const enabled = ref(false)
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await $fetch<{ notify_time: string | null; enabled: boolean }>(
      `${apiBase}/push/notification-setting`
    )
    notifyTime.value = res.notify_time ?? ''
    enabled.value = res.enabled
  } catch {
    toast.add({ title: '設定の読み込みに失敗しました', color: 'error' })
  }
})

async function save() {
  loading.value = true
  try {
    await $fetch(`${apiBase}/push/notification-setting`, {
      method: 'PUT',
      body: {
        notify_time: notifyTime.value || null,
        enabled: enabled.value,
      },
    })
    toast.add({ title: '設定を保存しました', color: 'success' })
  } catch {
    toast.add({ title: '設定の保存に失敗しました', color: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto">
    <h1 class="text-2xl font-bold mb-6">
      通知設定
    </h1>

    <UCard>
      <div class="space-y-6">
        <div>
          <p class="text-sm font-medium mb-1">
            定時通知
          </p>
          <p class="text-xs text-muted mb-3">
            毎日指定した時刻に、今日期限のタスクをプッシュ通知します
          </p>
          <UToggle
            v-model="enabled"
            label="定時通知を有効にする"
          />
        </div>

        <div v-if="enabled">
          <p class="text-sm font-medium mb-2">
            通知時刻
          </p>
          <input
            v-model="notifyTime"
            type="time"
            class="border border-default rounded-md px-3 py-2 text-sm bg-background text-foreground w-full"
          >
        </div>

        <UButton
          :loading="loading"
          :disabled="enabled && !notifyTime"
          block
          @click="save"
        >
          保存
        </UButton>
      </div>
    </UCard>

    <p class="text-xs text-muted mt-4 text-center">
      ※ プッシュ通知の受信には通知の許可が必要です（タスク一覧画面のベルアイコンからON）
    </p>
  </div>
</template>
