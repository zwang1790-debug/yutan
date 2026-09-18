import { useAuth } from '@/composables/useAuth'

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  timeoutMs?: number;
}

const DEFAULT_TIMEOUT_MS = 15_000

export async function http(url: string, options: FetchOptions = {}) {
  const { logout } = useAuth()
  
  const headers = new Headers(options.headers)

  // Handle Query Params
  let fullUrl = url
  if (options.params) {
    const searchParams = new URLSearchParams()
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      fullUrl += (url.includes('?') ? '&' : '?') + queryString
    }
  }

  const { params: _params, timeoutMs = DEFAULT_TIMEOUT_MS, signal: callerSignal, ...requestOptions } = options
  const timeoutController = new AbortController()
  let timeoutId: number | undefined
  let removeCallerAbortListener: (() => void) | undefined

  if (callerSignal) {
    const abortFromCaller = () => timeoutController.abort(callerSignal.reason)
    if (callerSignal.aborted) {
      abortFromCaller()
    } else {
      callerSignal.addEventListener('abort', abortFromCaller, { once: true })
      removeCallerAbortListener = () => callerSignal.removeEventListener('abort', abortFromCaller)
    }
  }

  const config: RequestInit = {
    ...requestOptions,
    credentials: options.credentials ?? 'same-origin',
    headers,
    signal: timeoutController.signal,
  }

  if (timeoutMs > 0) timeoutId = window.setTimeout(() => timeoutController.abort(), timeoutMs)

  let response: Response
  try {
    response = await fetch(fullUrl, config)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      if (callerSignal?.aborted) throw new Error('请求已取消')
      throw new Error('本地服务响应超时，请检查程序是否已启动，或关闭旧程序后重新打开最新版本')
    }
    throw error
  } finally {
    if (timeoutId !== undefined) window.clearTimeout(timeoutId)
    removeCallerAbortListener?.()
  }

  if (response.status === 401) {
    // Basic Auth failed or session expired
    logout()
    // Optional: Redirect to login handled by router or state change
    throw new Error('Unauthorized')
  }

  if (response.status === 402) {
    if (window.location.pathname !== '/license') window.location.assign('/license')
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'License required')
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const detail = typeof errorData.detail === 'string'
      ? errorData.detail
      : errorData.detail?.message
    throw new Error(detail || `HTTP error! status: ${response.status}`)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null
  }

  return response.json()
}
