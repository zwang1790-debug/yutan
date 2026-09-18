import type { InventoryRecord, InventoryStatus, ProfitEstimate, ResultInsights, ResultItem } from '@/types/result.d.ts'
import { http } from '@/lib/http'

export interface GetResultContentParams {
  recommended_only?: boolean;
  ai_recommended_only?: boolean;
  keyword_recommended_only?: boolean;
  include_hidden?: boolean;
  sort_by?: 'crawl_time' | 'publish_time' | 'price' | 'keyword_hit_count' | 'opportunity_score';
  sort_order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export async function getResultFiles(): Promise<string[]> {
  const data = await http('/api/results/files')
  return data.files || []
}

export async function deleteResultFile(filename: string): Promise<{ message: string }> {
  return await http(`/api/results/files/${filename}`, { method: 'DELETE' })
}

export async function getResultContent(
  filename: string,
  params: GetResultContentParams = {}
): Promise<{ total_items: number; items: ResultItem[] }> {
  return await http(`/api/results/${filename}`, { params: params as Record<string, any> })
}

export async function getResultInsights(filename: string): Promise<ResultInsights> {
  return await http(`/api/results/${filename}/insights`)
}

export async function getResultBlacklistRules(filename: string): Promise<{ keywords: string[] }> {
  return await http(`/api/results/${filename}/blacklist-rules`)
}

export async function updateResultBlacklistRules(filename: string, keywords: string[]): Promise<{ message: string; keywords: string[] }> {
  return await http(`/api/results/${filename}/blacklist-rules`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keywords }),
  })
}

export function buildResultExportUrl(filename: string, params: GetResultContentParams = {}): string {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.set(key, String(value))
    }
  })
  const queryString = searchParams.toString()
  return `/api/results/${encodeURIComponent(filename)}/export${queryString ? `?${queryString}` : ''}`
}

export function downloadResultExport(filename: string, params: GetResultContentParams = {}) {
  const url = buildResultExportUrl(filename, params)
  const link = document.createElement('a')
  link.href = url
  link.download = ''
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export async function updateItemStatus(filename: string, itemId: string, status: string): Promise<{ message: string; status: string }> {
  return await http(`/api/results/${filename}/items/${itemId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
}

export async function saveProfitEstimate(
  filename: string,
  itemId: string,
  estimate: Omit<ProfitEstimate, 'profit' | 'margin' | 'updated_at'>
): Promise<{ message: string; estimate: ProfitEstimate }> {
  return await http('/api/results/' + encodeURIComponent(filename) + '/items/' + encodeURIComponent(itemId) + '/profit-estimate', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(estimate),
  })
}

export type InventoryRecordPayload = {
  status: InventoryStatus;
  actual_purchase_price: number | null;
  actual_sale_price: number | null;
  actual_platform_fee: number;
  actual_shipping_cost: number;
  actual_other_cost: number;
  notes: string;
}

export async function saveInventoryRecord(
  filename: string,
  itemId: string,
  record: InventoryRecordPayload
): Promise<{ message: string; record: InventoryRecord }> {
  return await http('/api/results/' + encodeURIComponent(filename) + '/items/' + encodeURIComponent(itemId) + '/inventory', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(record),
  })
}
