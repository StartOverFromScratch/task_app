/**
 * SSR/CSR を意識して適切な API ベース URL を返す。
 * - サーバーサイド（Docker 内 SSR）: NUXT_API_BASE_SERVER（例: http://backend:8000）
 * - クライアントサイド: NUXT_PUBLIC_API_BASE（例: http://localhost:8000）
 */
export const useApiBase = (): string => {
  const config = useRuntimeConfig()
  if (import.meta.server && config.apiBaseServer) {
    return config.apiBaseServer as string
  }
  return config.public.apiBase
}
