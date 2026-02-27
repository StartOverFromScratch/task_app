export function useErrorToast() {
  const toast = useToast()

  function handle(e: unknown) {
    const err = e as { statusCode?: number, status?: number, data?: { detail?: string } }
    const status = err?.statusCode || err?.status
    const detail = err?.data?.detail ?? ''

    if (status === 400) {
      toast.add({ title: '操作エラー', description: detail || 'リクエストが不正です', color: 'error' })
    } else if (status === 404) {
      toast.add({ title: '見つかりません', description: '対象が見つかりませんでした', color: 'error' })
    } else if (status === 422) {
      toast.add({ title: '入力エラー', description: '入力内容を確認してください', color: 'error' })
    } else {
      toast.add({ title: 'エラーが発生しました', color: 'error' })
    }
  }

  return { handle }
}
