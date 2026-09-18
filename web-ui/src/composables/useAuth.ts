import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { wsService } from '@/services/websocket'

const SESSION_CHECK_ENDPOINT = '/auth/me'
const AUTH_REQUEST_TIMEOUT_MS = 15000
const username = ref<string | null>(localStorage.getItem('auth_username'))
const isLoggedIn = ref(localStorage.getItem('auth_logged_in') === 'true')
const sessionChecked = ref(false)
let sessionCheckPromise: Promise<boolean> | null = null

export interface AuthSetupStatus {
  registration_required: boolean
  registration_available: boolean
  password_min_length: number
}

export interface AuthActionResult {
  success: boolean
  message?: string
  status?: number
  username?: string
  recoveryCode?: string
}

async function responseMessage(response: Response): Promise<string> {
  const payload = await response.json().catch(() => ({}))
  return typeof payload.detail === 'string' ? payload.detail : ''
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), AUTH_REQUEST_TIMEOUT_MS)
  try {
    return await fetch(input, { ...init, signal: controller.signal })
  } finally {
    window.clearTimeout(timeout)
  }
}

export function useAuth() {
  const router = useRouter()

  const isAuthenticated = computed(() => isLoggedIn.value)

  function setAuthenticated(user: string) {
    username.value = user
    isLoggedIn.value = true
    sessionChecked.value = true
    sessionCheckPromise = Promise.resolve(true)

    localStorage.setItem('auth_username', user)
    localStorage.setItem('auth_logged_in', 'true')

    // 启动 WebSocket 连接
    wsService.start()
  }

  function clearLocalAuth() {
    username.value = null
    isLoggedIn.value = false
    localStorage.removeItem('auth_username')
    localStorage.removeItem('auth_logged_in')
    wsService.stop()
    sessionCheckPromise = null
  }

  function logout() {
    void fetch('/auth/logout', {
      method: 'POST',
      credentials: 'same-origin',
    }).catch(() => undefined)

    clearLocalAuth()

    if (router.currentRoute.value.name !== 'Login') {
      void router.replace({ name: 'Login' })
    }
  }

  async function getSetupStatus(): Promise<AuthSetupStatus> {
    const response = await fetchWithTimeout('/auth/setup', { credentials: 'same-origin' })
    if (!response.ok) throw new Error('Unable to load account setup status')
    return await response.json() as AuthSetupStatus
  }

  async function login(user: string, pass: string): Promise<AuthActionResult> {
    try {
      const response = await fetchWithTimeout('/auth/status', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: user, password: pass }),
      })

      if (response.ok) {
        const payload = await response.json().catch(() => ({}))
        setAuthenticated(typeof payload.username === 'string' ? payload.username : user)
        return { success: true, username: payload.username || user, recoveryCode: payload.recovery_code || undefined }
      }
      return { success: false, status: response.status, message: await responseMessage(response) }
    } catch (e) {
      console.error('Login error', e)
      return { success: false, message: '登录请求超时或服务未响应，请关闭旧程序后重新打开。' }
    }
  }

  async function register(user: string, pass: string, confirmPass: string): Promise<AuthActionResult> {
    try {
      const response = await fetchWithTimeout('/auth/register', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass, confirm_password: confirmPass }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) return { success: false, status: response.status, message: payload.detail }
      setAuthenticated(typeof payload.username === 'string' ? payload.username : user)
      return { success: true, username: payload.username || user, recoveryCode: payload.recovery_code }
    } catch (e) {
      console.error('Registration error', e)
      return { success: false }
    }
  }

  async function changePassword(currentPassword: string, newPassword: string, confirmPassword: string): Promise<AuthActionResult> {
    try {
      const response = await fetchWithTimeout('/auth/password', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword, confirm_password: confirmPassword }),
      })
      if (!response.ok) return { success: false, status: response.status, message: await responseMessage(response) }
      const payload = await response.json().catch(() => ({}))
      setAuthenticated(typeof payload.username === 'string' ? payload.username : username.value || '')
      return { success: true }
    } catch (e) {
      console.error('Password change error', e)
      return { success: false }
    }
  }

  async function generateRecoveryCode(currentPassword: string): Promise<AuthActionResult> {
    try {
      const response = await fetch('/auth/recovery-code', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: currentPassword }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) return { success: false, status: response.status, message: payload.detail }
      return { success: true, recoveryCode: payload.recovery_code }
    } catch (e) {
      console.error('Recovery code error', e)
      return { success: false }
    }
  }

  async function recoverPassword(user: string, recoveryCode: string, newPassword: string, confirmPassword: string): Promise<AuthActionResult> {
    try {
      const response = await fetchWithTimeout('/auth/recover', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, recovery_code: recoveryCode, new_password: newPassword, confirm_password: confirmPassword }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) return { success: false, status: response.status, message: payload.detail }
      setAuthenticated(typeof payload.username === 'string' ? payload.username : user)
      return { success: true, username: payload.username || user }
    } catch (e) {
      console.error('Password recovery error', e)
      return { success: false }
    }
  }

  async function restoreSession(): Promise<boolean> {
    if (sessionCheckPromise) return sessionCheckPromise

    sessionCheckPromise = (async () => {
      try {
        const response = await fetchWithTimeout(SESSION_CHECK_ENDPOINT, {
          credentials: 'same-origin',
        })
        if (!response.ok) {
          clearLocalAuth()
          return false
        }

        const payload = await response.json().catch(() => ({}))
        if (typeof payload.username !== 'string') {
          clearLocalAuth()
          return false
        }
        setAuthenticated(payload.username)
        return true
      } catch {
        clearLocalAuth()
        return false
      } finally {
        sessionChecked.value = true
      }
    })()

    return sessionCheckPromise
  }

  return {
    username,
    isAuthenticated,
    sessionChecked,
    login,
    getSetupStatus,
    register,
    changePassword,
    generateRecoveryCode,
    recoverPassword,
    logout,
    restoreSession,
  }
}
