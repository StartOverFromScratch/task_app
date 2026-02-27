import type { CaptureCreateRequest, CaptureUpdateRequest } from '~/types/capture'

export function useCapture() {
  const captureStore = useCaptureStore()
  const { handle } = useErrorToast()
  const toast = useToast()

  async function fetchCaptures(isResolved?: boolean) {
    try {
      const items = await captureRepository.fetchAll(isResolved)
      captureStore.setAll(items)
    } catch (e) { handle(e) }
  }

  async function createCapture(data: CaptureCreateRequest) {
    try {
      const item = await captureRepository.create(data)
      captureStore.upsert(item)
      toast.add({ title: '記録しました', color: 'success' })
    } catch (e) { handle(e) }
  }

  async function updateCapture(id: number, data: CaptureUpdateRequest) {
    try {
      const item = await captureRepository.update(id, data)
      captureStore.upsert(item)
    } catch (e) { handle(e) }
  }

  async function deleteCapture(id: number) {
    try {
      await captureRepository.remove(id)
      captureStore.remove(id)
    } catch (e) { handle(e) }
  }

  return { fetchCaptures, createCapture, updateCapture, deleteCapture }
}
