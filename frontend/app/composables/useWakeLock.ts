export function useWakeLock() {
  const isActive = ref(false)
  const isSupported = ref(true) // 常に表示し、非対応時はトーストで通知
  let sentinel: WakeLockSentinel | null = null
  const toast = useToast()

  async function enable() {
    if (!('wakeLock' in navigator)) {
      toast.add({ title: 'このブラウザはスリープ防止に対応していません', color: 'warning' })
      return
    }
    try {
      sentinel = await navigator.wakeLock.request('screen')
      isActive.value = true
      sentinel.addEventListener('release', () => {
        isActive.value = false
        sentinel = null
      })
    } catch {
      toast.add({ title: 'スリープ防止の開始に失敗しました', color: 'error' })
    }
  }

  async function disable() {
    await sentinel?.release()
    sentinel = null
    isActive.value = false
  }

  async function toggle() {
    isActive.value ? await disable() : await enable()
  }

  onUnmounted(() => {
    sentinel?.release()
  })

  return { isActive, isSupported, toggle }
}
