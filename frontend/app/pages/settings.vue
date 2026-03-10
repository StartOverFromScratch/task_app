<script setup lang="ts">
const apiBase = useApiBase()
const toast = useToast()

const notifyTime1 = ref('09:00')
const notifyTime2 = ref('16:00')
const enabled = ref(false)
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await $fetch<{ notify_time_1: string | null; notify_time_2: string | null; enabled: boolean }>(
      `${apiBase}/push/notification-setting`
    )
    notifyTime1.value = res.notify_time_1 ?? '09:00'
    notifyTime2.value = res.notify_time_2 ?? '16:00'
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
        notify_time_1: notifyTime1.value || null,
        notify_time_2: notifyTime2.value || null,
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
          <USwitch
            v-model="enabled"
            label="定時通知を有効にする"
          />
        </div>

        <div class="space-y-4">
          <div>
            <p class="text-sm font-medium mb-1">
              通知時刻 1
            </p>
            <input
              v-model="notifyTime1"
              type="time"
              class="border border-default rounded-md px-3 py-2 text-sm bg-background text-foreground w-full"
            >
          </div>
          <div>
            <p class="text-sm font-medium mb-1">
              通知時刻 2
            </p>
            <input
              v-model="notifyTime2"
              type="time"
              class="border border-default rounded-md px-3 py-2 text-sm bg-background text-foreground w-full"
            >
          </div>
        </div>

        <UButton
          :loading="loading"
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
