<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Check, Copy, Eye, EyeOff, KeyRound, LogOut, ShieldCheck, UserCircle } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { toast } from '@/components/ui/toast'

const open = defineModel<boolean>('open', { default: false })
const { t } = useI18n()
const { username, changePassword, generateRecoveryCode, logout } = useAuth()

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const recoveryPassword = ref('')
const recoveryCode = ref('')
const isChangingPassword = ref(false)
const isGeneratingCode = ref(false)
const codeCopied = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const showRecoveryPassword = ref(false)

function showError(title: string, description?: string) {
  toast({ title, description, variant: 'destructive' })
}

async function handleChangePassword() {
  if (!currentPassword.value || !newPassword.value || newPassword.value !== confirmPassword.value) {
    showError(t('settings.security.passwordChangeFailed'), t('settings.security.passwordMismatch'))
    return
  }
  isChangingPassword.value = true
  try {
    const result = await changePassword(currentPassword.value, newPassword.value, confirmPassword.value)
    if (!result.success) {
      showError(t('settings.security.passwordChangeFailed'), result.message)
      return
    }
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    toast({ title: t('settings.security.passwordChanged') })
  } finally {
    isChangingPassword.value = false
  }
}

async function handleGenerateRecoveryCode() {
  if (!recoveryPassword.value) {
    showError(t('settings.security.recoveryCodeFailed'), t('settings.security.currentPasswordRequired'))
    return
  }
  isGeneratingCode.value = true
  try {
    const result = await generateRecoveryCode(recoveryPassword.value)
    if (!result.success) {
      showError(t('settings.security.recoveryCodeFailed'), result.message)
      return
    }
    recoveryCode.value = result.recoveryCode || ''
    recoveryPassword.value = ''
    codeCopied.value = false
    toast({ title: t('settings.security.recoveryCodeGenerated') })
  } finally {
    isGeneratingCode.value = false
  }
}

async function copyRecoveryCode() {
  if (!recoveryCode.value || !navigator.clipboard) return
  try {
    await navigator.clipboard.writeText(recoveryCode.value)
    codeCopied.value = true
    window.setTimeout(() => { codeCopied.value = false }, 1800)
  } catch {
    codeCopied.value = false
  }
}

function handleLogout() {
  open.value = false
  logout()
}
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent class="max-h-[88dvh] overflow-y-auto sm:max-w-[640px]">
      <DialogHeader>
        <div class="flex items-start gap-3">
          <div class="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
            <ShieldCheck class="size-5" />
          </div>
          <div>
            <DialogTitle>{{ t('header.accountSecurity') }}</DialogTitle>
            <DialogDescription class="mt-1">{{ t('header.accountSecurityDescription') }}</DialogDescription>
          </div>
        </div>
      </DialogHeader>

      <div class="grid gap-5 py-2">
        <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="flex items-center gap-3">
            <div class="flex size-10 items-center justify-center rounded-full bg-slate-900 text-white"><UserCircle class="size-5" /></div>
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">{{ t('header.signedInAs') }}</p>
              <p class="mt-1 font-bold text-slate-900">{{ username || t('common.unknown') }}</p>
            </div>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-200 p-4 sm:p-5">
          <div class="mb-4 flex items-start gap-3">
            <KeyRound class="mt-0.5 size-5 text-sky-700" />
            <div>
              <h3 class="font-bold text-slate-900">{{ t('settings.security.passwordTitle') }}</h3>
              <p class="mt-1 text-sm leading-5 text-slate-500">{{ t('settings.security.passwordDescription') }}</p>
            </div>
          </div>
          <form class="grid gap-4" @submit.prevent="handleChangePassword">
            <div class="grid gap-2">
              <Label for="header-current-password">{{ t('settings.security.currentPassword') }}</Label>
              <div class="relative"><Input id="header-current-password" v-model="currentPassword" :type="showCurrentPassword ? 'text' : 'password'" class="pr-11" autocomplete="current-password" /><button type="button" class="password-toggle" :aria-label="showCurrentPassword ? t('login.hidePassword') : t('login.showPassword')" @click="showCurrentPassword = !showCurrentPassword"><EyeOff v-if="showCurrentPassword" class="size-4" /><Eye v-else class="size-4" /></button></div>
            </div>
            <div class="grid gap-2 sm:grid-cols-2 sm:gap-3">
              <div class="grid gap-2"><Label for="header-new-password">{{ t('settings.security.newPassword') }}</Label><div class="relative"><Input id="header-new-password" v-model="newPassword" :type="showNewPassword ? 'text' : 'password'" class="pr-11" autocomplete="new-password" /><button type="button" class="password-toggle" :aria-label="showNewPassword ? t('login.hidePassword') : t('login.showPassword')" @click="showNewPassword = !showNewPassword"><EyeOff v-if="showNewPassword" class="size-4" /><Eye v-else class="size-4" /></button></div></div>
              <div class="grid gap-2"><Label for="header-confirm-password">{{ t('settings.security.confirmPassword') }}</Label><div class="relative"><Input id="header-confirm-password" v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" class="pr-11" autocomplete="new-password" /><button type="button" class="password-toggle" :aria-label="showConfirmPassword ? t('login.hidePassword') : t('login.showPassword')" @click="showConfirmPassword = !showConfirmPassword"><EyeOff v-if="showConfirmPassword" class="size-4" /><Eye v-else class="size-4" /></button></div></div>
            </div>
            <div><Button type="submit" :disabled="isChangingPassword">{{ isChangingPassword ? t('common.saving') : t('settings.security.changePassword') }}</Button></div>
          </form>
        </section>

        <section class="rounded-2xl border border-amber-200 bg-amber-50/50 p-4 sm:p-5">
          <h3 class="font-bold text-amber-950">{{ t('settings.security.recoveryTitle') }}</h3>
          <p class="mt-1 text-sm leading-5 text-amber-900/75">{{ t('settings.security.recoveryDescription') }}</p>
          <form class="mt-4 grid gap-3" @submit.prevent="handleGenerateRecoveryCode">
            <div class="grid gap-2"><Label for="header-recovery-password">{{ t('settings.security.currentPassword') }}</Label><div class="relative"><Input id="header-recovery-password" v-model="recoveryPassword" :type="showRecoveryPassword ? 'text' : 'password'" class="border-amber-200 bg-white pr-11" autocomplete="current-password" /><button type="button" class="password-toggle" :aria-label="showRecoveryPassword ? t('login.hidePassword') : t('login.showPassword')" @click="showRecoveryPassword = !showRecoveryPassword"><EyeOff v-if="showRecoveryPassword" class="size-4" /><Eye v-else class="size-4" /></button></div></div>
            <div><Button type="submit" variant="outline" :disabled="isGeneratingCode">{{ isGeneratingCode ? t('common.loading') : t('settings.security.generateRecoveryCode') }}</Button></div>
          </form>
          <div v-if="recoveryCode" class="mt-4 rounded-xl border border-amber-200 bg-white p-3" role="status">
            <p class="text-sm font-bold text-amber-950">{{ t('settings.security.recoveryCodeShown') }}</p>
            <div class="mt-3 flex items-center gap-2"><code class="min-w-0 flex-1 rounded-lg bg-amber-50 px-3 py-2 text-center text-base font-black tracking-[0.14em] text-amber-950">{{ recoveryCode }}</code><Button type="button" variant="outline" size="icon-sm" :aria-label="codeCopied ? t('settings.security.recoveryCodeCopied') : t('settings.security.copyRecoveryCode')" @click="copyRecoveryCode"><Check v-if="codeCopied" class="text-emerald-600" /><Copy v-else /></Button></div>
            <p class="mt-3 text-xs leading-5 text-amber-900/75">{{ t('settings.security.recoveryWarning') }}</p>
          </div>
        </section>
      </div>

      <DialogFooter class="border-t border-slate-100 pt-4 sm:justify-between">
        <p class="text-xs text-slate-400">{{ t('header.localAccountHint') }}</p>
        <Button variant="ghost" class="text-rose-600 hover:bg-rose-50 hover:text-rose-700" @click="handleLogout"><LogOut class="size-4" />{{ t('header.logout') }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.password-toggle { @apply absolute right-1 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40; }
</style>
