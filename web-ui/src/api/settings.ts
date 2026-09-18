import { http } from '@/lib/http'

export interface NotificationSettings {
  NTFY_TOPIC_URL?: string
  GOTIFY_URL?: string
  GOTIFY_TOKEN?: string
  BARK_URL?: string
  WX_BOT_URL?: string
  TELEGRAM_BOT_TOKEN?: string
  TELEGRAM_CHAT_ID?: string
  TELEGRAM_API_BASE_URL?: string
  WEBHOOK_URL?: string
  WEBHOOK_METHOD?: string
  WEBHOOK_HEADERS?: string
  WEBHOOK_CONTENT_TYPE?: string
  WEBHOOK_QUERY_PARAMETERS?: string
  WEBHOOK_BODY?: string
  PCURL_TO_MOBILE?: boolean
  BARK_URL_SET?: boolean
  GOTIFY_TOKEN_SET?: boolean
  WX_BOT_URL_SET?: boolean
  TELEGRAM_BOT_TOKEN_SET?: boolean
  WEBHOOK_URL_SET?: boolean
  WEBHOOK_HEADERS_SET?: boolean
  CONFIGURED_CHANNELS?: string[]
}

export interface NotificationSettingsUpdate {
  NTFY_TOPIC_URL?: string | null
  GOTIFY_URL?: string | null
  GOTIFY_TOKEN?: string | null
  BARK_URL?: string | null
  WX_BOT_URL?: string | null
  TELEGRAM_BOT_TOKEN?: string | null
  TELEGRAM_CHAT_ID?: string | null
  TELEGRAM_API_BASE_URL?: string | null
  WEBHOOK_URL?: string | null
  WEBHOOK_METHOD?: string | null
  WEBHOOK_HEADERS?: string | null
  WEBHOOK_CONTENT_TYPE?: string | null
  WEBHOOK_QUERY_PARAMETERS?: string | null
  WEBHOOK_BODY?: string | null
  PCURL_TO_MOBILE?: boolean
}

export interface NotificationTestResponse {
  message: string
  results: Record<string, {
    label: string
    success: boolean
    message: string
  }>
}

export interface AiSettings {
  OPENAI_API_KEY?: string
  OPENAI_BASE_URL?: string
  OPENAI_MODEL_NAME?: string
  PROXY_URL?: string
}

export interface RotationSettings {
  ACCOUNT_ROTATION_ENABLED?: boolean
  ACCOUNT_ROTATION_MODE?: string
  ACCOUNT_ROTATION_RETRY_LIMIT?: number
  ACCOUNT_BLACKLIST_TTL?: number
  ACCOUNT_STATE_DIR?: string
  PROXY_ROTATION_ENABLED?: boolean
  PROXY_ROTATION_MODE?: string
  PROXY_POOL?: string
  PROXY_ROTATION_RETRY_LIMIT?: number
  PROXY_BLACKLIST_TTL?: number
}

export interface SystemStatus {
  scraper_running: boolean
  running_task_ids?: number[]
  ai_configured?: boolean
  notification_configured?: boolean
  headless_mode?: boolean
  running_in_docker?: boolean
  login_state_file: {
    exists: boolean
    path: string
  }
  env_file: {
    exists: boolean
    openai_api_key_set: boolean
    openai_base_url_set: boolean
    openai_model_name_set: boolean
    ntfy_topic_url_set: boolean
    gotify_url_set: boolean
    gotify_token_set: boolean
    bark_url_set: boolean
    wx_bot_url_set: boolean
    telegram_bot_token_set: boolean
    telegram_chat_id_set: boolean
    webhook_url_set: boolean
    webhook_headers_set: boolean
  }
  configured_notification_channels?: string[]
}

export interface DiagnosticCheck {
  key: string
  label: string
  status: 'pass' | 'warn' | 'info'
  detail: string
}

export interface DiagnosticsResponse {
  success: boolean
  summary: string
  checks: DiagnosticCheck[]
}

export interface ReleaseInfo {
  product_name: string
  version: string
  release_date: string
  build_type: string
  support_items: string[]
  release_notes: string[]
  support_steps: string[]
}

export type LocalizedText = Record<'zh' | 'en', string>

export interface ProductPlan {
  id: string
  kind: 'software' | 'service'
  name: LocalizedText
  description: LocalizedText
  price: number
  currency: 'CNY'
  billing_period: '7_days' | 'monthly' | 'annual' | 'one_time'
  availability: 'available' | 'coming_soon'
  badge: LocalizedText
  features: LocalizedText[]
  note: LocalizedText
  recommended: boolean
}

export interface ProductPricing {
  product_name: LocalizedText
  positioning: LocalizedText
  pricing_version: string
  last_reviewed: string
  commercial_stage: 'manual_delivery'
  plans: ProductPlan[]
  policies: Record<string, LocalizedText>
  sales_guardrails: LocalizedText[]
}

export interface LoginStateStatus {
  exists: boolean
  valid_json: boolean
  path: string
  updated_at: number | null
  message: string
}

export interface LicenseStatus {
  state: 'trial' | 'licensed' | 'expired' | 'blocked'
  code: string | null
  message: string
  entitled: boolean
  trial_started_at: number | null
  trial_expires_at: number | null
  license_id: string | null
  plan: string | null
  issued_at: number | null
  expires_at: number | null
  device_hash: string
  version: string | null
  clock_tampered: boolean
}

export async function getLicenseStatus(): Promise<LicenseStatus> {
  return await http('/api/license/status')
}

export async function activateLicense(code: string): Promise<LicenseStatus> {
  return await http('/api/license/activate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  })
}

export async function getNotificationSettings(): Promise<NotificationSettings> {
  return await http('/api/settings/notifications')
}

export async function updateNotificationSettings(settings: NotificationSettingsUpdate): Promise<{ message: string; configured_channels: string[] }> {
  return await http('/api/settings/notifications', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  })
}

export async function testNotificationSettings(
  payload: { channel?: string; settings: NotificationSettingsUpdate }
): Promise<NotificationTestResponse> {
  return await http('/api/settings/notifications/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function getAiSettings(): Promise<AiSettings> {
  return await http('/api/settings/ai')
}

export async function updateAiSettings(settings: AiSettings): Promise<void> {
  await http('/api/settings/ai', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  })
}

export async function getRotationSettings(): Promise<RotationSettings> {
  return await http('/api/settings/rotation')
}

export async function updateRotationSettings(settings: RotationSettings): Promise<void> {
  await http('/api/settings/rotation', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  })
}

export async function testAiSettings(settings: AiSettings): Promise<{ success: boolean; message: string; response?: string }> {
  return await http('/api/settings/ai/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  })
}

export async function getSystemStatus(): Promise<SystemStatus> {
  return await http('/api/settings/status')
}

export async function getDiagnostics(): Promise<DiagnosticsResponse> {
  return await http('/api/settings/diagnostics')
}

export async function getReleaseInfo(): Promise<ReleaseInfo> {
  return await http('/api/settings/release')
}

export async function getProductPricing(): Promise<ProductPricing> {
  return await http('/api/settings/pricing')
}

export async function updateLoginState(content: string): Promise<{ message: string }> {
  return await http('/api/login-state', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  })
}

export async function deleteLoginState(): Promise<{ message: string }> {
  return await http('/api/login-state', { method: 'DELETE' })
}

export async function getLoginStateStatus(): Promise<LoginStateStatus> {
  return await http('/api/login-state/status')
}

export interface BackupStatus {
  items: Record<string, number>
  total_bytes: number
  full_backup_bytes: number
  safe_backup_excludes: string[]
}

export async function getBackupStatus(): Promise<BackupStatus> {
  return await http('/api/backup/status')
}

export async function restoreBackup(file: File): Promise<{ message: string; safety_backup: string; backup_type: 'safe' | 'full'; restart_recommended: boolean }> {
  return await http('/api/backup/restore', {
    method: 'POST',
    headers: { 'Content-Type': 'application/zip' },
    body: file,
  })
}

export function downloadFullBackup() {
  window.location.href = '/api/backup/download/full'
}

export function downloadDiagnosticBundle() {
  window.location.href = '/api/backup/diagnostic'
}
