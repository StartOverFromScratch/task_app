export function usePushNotification() {
  const isSubscribed = ref(false)
  const isSupported = ref(false)
  const toast = useToast()
  const apiBase = useApiBase()

  onMounted(async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return
    isSupported.value = true

    const reg = await navigator.serviceWorker.getRegistration('/sw.js')
    if (reg) {
      const sub = await reg.pushManager.getSubscription()
      isSubscribed.value = !!sub
    }
  })

  async function subscribe() {
    try {
      const reg = await navigator.serviceWorker.register('/sw.js')
      await navigator.serviceWorker.ready

      const keyRes = await $fetch<{ public_key: string }>(`${apiBase}/push/vapid-public-key`)
      const applicationServerKey = urlBase64ToUint8Array(keyRes.public_key)

      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey,
      })

      const json = sub.toJSON()
      await $fetch(`${apiBase}/push/subscribe`, {
        method: 'POST',
        body: {
          endpoint: json.endpoint,
          keys: { p256dh: json.keys!.p256dh, auth: json.keys!.auth },
        },
      })

      isSubscribed.value = true
      toast.add({ title: '通知を有効にしました', color: 'success' })
    } catch (e) {
      console.error('[PushNotification] subscribe error:', e)
      const msg = e instanceof Error ? e.message : String(e)
      toast.add({ title: '通知の登録に失敗しました', description: msg, color: 'error' })
    }
  }

  async function unsubscribe() {
    try {
      const reg = await navigator.serviceWorker.getRegistration('/sw.js')
      if (!reg) return
      const sub = await reg.pushManager.getSubscription()
      if (!sub) { isSubscribed.value = false; return }

      const json = sub.toJSON()
      await $fetch(`${apiBase}/push/subscribe`, {
        method: 'DELETE',
        body: {
          endpoint: json.endpoint,
          keys: { p256dh: json.keys!.p256dh, auth: json.keys!.auth },
        },
      }).catch(() => {})

      await sub.unsubscribe()
      isSubscribed.value = false
      toast.add({ title: '通知を無効にしました', color: 'neutral' })
    } catch {
      toast.add({ title: '通知の解除に失敗しました', color: 'error' })
    }
  }

  async function toggle() {
    isSubscribed.value ? await unsubscribe() : await subscribe()
  }

  async function sendTodayDue() {
    try {
      const res = await $fetch<{ sent: number; task_count: number }>(`${apiBase}/push/send-today-due`, { method: 'POST' })
      toast.add({ title: `通知を送信しました（今日の期限: ${res.task_count ?? 0}件）`, color: 'success' })
    } catch {
      toast.add({ title: '通知の送信に失敗しました', color: 'error' })
    }
  }

  return { isSubscribed, isSupported, toggle, sendTodayDue }
}

function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  const arr = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; i++) arr[i] = rawData.charCodeAt(i)
  return arr.buffer as ArrayBuffer
}
