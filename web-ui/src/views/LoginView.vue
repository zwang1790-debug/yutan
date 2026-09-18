<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import LocaleToggle from '@/components/layout/LocaleToggle.vue'
import BrandMark from '@/components/layout/BrandMark.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Check, Copy, Eye, EyeOff } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

type AuthMode = 'login' | 'register' | 'recover'

const mode = ref<AuthMode>('login')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const recoveryCode = ref('')
const isLoading = ref(false)
const error = ref('')
const setupLoaded = ref(false)
const registrationAvailable = ref(false)
const passwordMinLength = ref(8)
const issuedRecoveryCode = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const recoveryCodeCopied = ref(false)

const { login, register, recoverPassword, getSetupStatus } = useAuth()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()

function redirectAfterAuth() {
  const requestedRedirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
  const redirectPath = requestedRedirect.startsWith('/') && !requestedRedirect.startsWith('//')
    ? requestedRedirect
    : '/dashboard'
  router.push(redirectPath)
}

function switchMode(nextMode: AuthMode) {
  mode.value = nextMode
  error.value = ''
  password.value = ''
  confirmPassword.value = ''
  recoveryCode.value = ''
  issuedRecoveryCode.value = ''
  showPassword.value = false
  showConfirmPassword.value = false
  recoveryCodeCopied.value = false
}

async function copyRecoveryCode() {
  if (!issuedRecoveryCode.value || !navigator.clipboard) return
  try {
    await navigator.clipboard.writeText(issuedRecoveryCode.value)
    recoveryCodeCopied.value = true
    window.setTimeout(() => { recoveryCodeCopied.value = false }, 1800)
  } catch {
    recoveryCodeCopied.value = false
  }
}

function validateForm() {
  if (!username.value.trim() || !password.value) {
    error.value = t('login.errors.missingCredentials')
    return false
  }
  if (mode.value !== 'login' && password.value.length < passwordMinLength.value) {
    error.value = t('login.errors.passwordTooShort', { count: passwordMinLength.value })
    return false
  }
  if (mode.value !== 'login' && password.value !== confirmPassword.value) {
    error.value = t('login.errors.passwordMismatch')
    return false
  }
  if (mode.value === 'recover' && !recoveryCode.value.trim()) {
    error.value = t('login.errors.missingRecoveryCode')
    return false
  }
  return true
}

async function handleSubmit() {
  if (!validateForm()) return
  isLoading.value = true
  error.value = ''
  try {
    if (mode.value === 'register') {
      const result = await register(username.value, password.value, confirmPassword.value)
      if (result.success) {
        issuedRecoveryCode.value = result.recoveryCode || ''
        return
      }
      error.value = result.message || t('login.errors.registerFailed')
      return
    }

    if (mode.value === 'recover') {
      const result = await recoverPassword(username.value, recoveryCode.value, password.value, confirmPassword.value)
      if (result.success) {
        redirectAfterAuth()
      } else {
        error.value = result.message || t('login.errors.recoveryFailed')
      }
      return
    }

    const result = await login(username.value, password.value)
    if (result.success) {
      if (result.recoveryCode) {
        issuedRecoveryCode.value = result.recoveryCode
      } else {
        redirectAfterAuth()
      }
    } else if (result.status === 409) {
      mode.value = 'register'
      error.value = t('login.errors.registrationRequired')
    } else {
      error.value = result.message || t('login.errors.invalidCredentials')
    }
  } catch {
    error.value = t('login.errors.unexpected')
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  try {
    const setup = await getSetupStatus()
    passwordMinLength.value = setup.password_min_length || 8
    registrationAvailable.value = setup.registration_available
    if (setup.registration_required) mode.value = 'register'
  } catch {
    // Older backend builds can still use the normal login form.
  } finally {
    setupLoaded.value = true
  }
})
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-100 px-4 py-10">
    <div aria-hidden="true" class="absolute inset-0">
      <div class="absolute left-[-10%] top-[-10%] h-72 w-72 rounded-full bg-primary/10 blur-3xl"></div>
      <div class="absolute bottom-[-10%] right-[-5%] h-72 w-72 rounded-full bg-blue-300/10 blur-3xl"></div>
    </div>
    <div class="absolute right-6 top-6"><LocaleToggle /></div>

    <Card class="app-surface relative z-10 w-full max-w-md border-none">
      <CardHeader>
        <div class="mb-3 flex items-center justify-center gap-3">
          <BrandMark :size="52" :label="t('app.name')" />
          <div class="text-left">
            <p class="text-lg font-black tracking-tight text-slate-950">{{ t('app.name') }}</p>
            <p class="mt-1 text-xs font-medium text-slate-500">{{ t('app.tagline') }}</p>
          </div>
        </div>
        <CardTitle class="text-center text-2xl">
          {{ mode === 'login' ? t('login.title') : mode === 'register' ? t('login.registerTitle') : t('login.recoverTitle') }}
        </CardTitle>
        <CardDescription class="text-center">
          {{ mode === 'login' ? t('login.description') : mode === 'register' ? t('login.registerDescription') : t('login.recoverDescription') }}
        </CardDescription>
        <p v-if="mode !== 'login'" class="mt-3 text-center text-xs leading-5 text-slate-500">
          {{ t('login.passwordHint', { count: passwordMinLength }) }}
        </p>
      </CardHeader>

      <div v-if="issuedRecoveryCode" class="mx-6 mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4" role="status">
        <p class="text-sm font-bold text-amber-900">{{ t('login.recoveryCodeTitle') }}</p>
        <p class="mt-1 text-xs leading-5 text-amber-800">{{ t('login.recoveryCodeDescription') }}</p>
        <div class="mt-3 flex items-center gap-2 rounded-lg bg-white p-2 shadow-sm">
          <code class="min-w-0 flex-1 px-1 py-1 text-center text-lg font-black tracking-[0.18em] text-amber-950">{{ issuedRecoveryCode }}</code>
          <Button type="button" variant="outline" size="icon-sm" :aria-label="recoveryCodeCopied ? t('login.recoveryCodeCopied') : t('login.copyRecoveryCode')" :title="recoveryCodeCopied ? t('login.recoveryCodeCopied') : t('login.copyRecoveryCode')" @click="copyRecoveryCode">
            <Check v-if="recoveryCodeCopied" class="text-emerald-600" />
            <Copy v-else />
          </Button>
        </div>
        <Button class="mt-4 w-full" type="button" @click="redirectAfterAuth">{{ t('login.continueToApp') }}</Button>
      </div>

      <form v-else @submit.prevent="handleSubmit">
        <CardContent class="grid gap-4">
          <div class="grid gap-2">
            <Label for="username">{{ t('login.username') }}</Label>
            <Input id="username" v-model="username" type="text" :placeholder="mode === 'register' ? t('login.usernamePlaceholder') : 'admin'" required autocomplete="username" />
          </div>

          <div v-if="mode === 'recover'" class="grid gap-2">
            <Label for="recovery-code">{{ t('login.recoveryCode') }}</Label>
            <Input id="recovery-code" v-model="recoveryCode" type="text" placeholder="AB12-CD34-EF56" required autocomplete="off" />
          </div>

          <div class="grid gap-2">
            <Label for="password">{{ mode === 'recover' ? t('login.newPassword') : t('login.password') }}</Label>
            <div class="relative">
              <Input id="password" v-model="password" :type="showPassword ? 'text' : 'password'" class="pr-11" required :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" />
              <button type="button" class="absolute right-1 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40" :aria-label="showPassword ? t('login.hidePassword') : t('login.showPassword')" @click="showPassword = !showPassword">
                <EyeOff v-if="showPassword" class="size-4" />
                <Eye v-else class="size-4" />
              </button>
            </div>
          </div>

          <div v-if="mode !== 'login'" class="grid gap-2">
            <Label for="confirm-password">{{ t('login.confirmPassword') }}</Label>
            <div class="relative">
              <Input id="confirm-password" v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" class="pr-11" required autocomplete="new-password" />
              <button type="button" class="absolute right-1 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40" :aria-label="showConfirmPassword ? t('login.hidePassword') : t('login.showPassword')" @click="showConfirmPassword = !showConfirmPassword">
                <EyeOff v-if="showConfirmPassword" class="size-4" />
                <Eye v-else class="size-4" />
              </button>
            </div>
          </div>

          <div v-if="error" class="text-sm font-medium text-red-600" role="alert">{{ error }}</div>
        </CardContent>
        <CardFooter class="grid gap-3">
          <Button class="w-full" type="submit" :disabled="isLoading || !setupLoaded">
            {{ isLoading ? t('login.submitting') : mode === 'login' ? t('login.submit') : mode === 'register' ? t('login.registerSubmit') : t('login.recoverSubmit') }}
          </Button>
          <div class="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs font-semibold text-slate-500">
            <button v-if="mode !== 'login'" type="button" class="text-primary hover:underline" @click="switchMode('login')">{{ t('login.backToLogin') }}</button>
            <button v-if="mode === 'login'" type="button" class="text-primary hover:underline" @click="switchMode('recover')">{{ t('login.forgotPassword') }}</button>
            <button v-if="mode === 'login' && registrationAvailable" type="button" class="text-primary hover:underline" @click="switchMode('register')">{{ t('login.createAccount') }}</button>
          </div>
        </CardFooter>
      </form>
    </Card>
  </div>
</template>
