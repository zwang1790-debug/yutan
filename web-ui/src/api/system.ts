import { http } from '@/lib/http'

export async function openExternalUrl(url: string) {
  return http('/api/system/open-external', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
}
