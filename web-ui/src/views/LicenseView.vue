<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ShieldCheck, Copy, Check, KeyRound, RefreshCw } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { getLicenseStatus, activateLicense, type LicenseStatus } from '@/api/settings'

const { t } = useI18n()
const status = ref<LicenseStatus | null>(null)
const code = ref('')
const loading = ref(true)
const activating = ref(false)
const copied = ref(false)
const error = ref('')

const stateLabel = computed(() => status.value ? t(`license.states.${status.value.state}`) : t('common.loading'))
const stateClass = computed(() => status.value?.entitled ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-900')
const expiresAt = computed(() => status.value?.expires_at || status.value?.trial_expires_at)
const isTrial = computed(() => status.value?.state === 'trial' || status.value?.plan === 'trial')

function formatDate(value: number | null | undefined) {
  return value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value * 1000)) : '-'
}

async function load() {
  loading.value = true
  error.value = ''
  try { status.value = await getLicenseStatus() } catch (cause) { error.value = (cause as Error).message } finally { loading.value = false }
}

async function activate() {
  if (!code.value.trim()) return
  activating.value = true
  error.value = ''
  try { status.value = await activateLicense(code.value.trim()); code.value = '' } catch (cause) { error.value = (cause as Error).message } finally { activating.value = false }
}

async function copyDeviceHash() {
  if (!status.value) return
  await navigator.clipboard.writeText(status.value.device_hash)
  copied.value = true
  window.setTimeout(() => { copied.value = false }, 1600)
}

onMounted(load)
</script>

<template>
  <div class="license-page page-shell relative space-y-5 overflow-hidden rounded-[28px] p-1.5 sm:p-2">
    <section class="relative overflow-hidden rounded-2xl border border-slate-700/70 bg-[#102b42] p-6 text-white shadow-[0_22px_60px_-28px_rgba(15,23,42,0.78)] sm:p-8">
      <div class="relative flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div class="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.16em] text-lime-200"><ShieldCheck class="h-4 w-4" />{{ t('license.eyebrow') }}</div>
          <h1 class="mt-3 text-3xl font-black tracking-tight">{{ t('license.title') }}</h1>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-white/70">{{ t('license.description') }}</p>
        </div>
        <span v-if="status" class="w-fit rounded-full px-3 py-1.5 text-sm font-black" :class="stateClass">{{ stateLabel }}</span>
      </div>
    </section>

    <div v-if="loading" class="h-64 animate-pulse rounded-2xl bg-white/70" />
    <div v-else class="grid gap-4 lg:grid-cols-[1fr_1.15fr]">
      <Card class="app-surface overflow-hidden border-none">
        <CardHeader class="border-b border-[#d8ebf7] bg-[#eaf7ff]"><CardTitle>{{ t('license.currentTitle') }}</CardTitle><CardDescription>{{ status?.message }}</CardDescription></CardHeader>
        <CardContent class="space-y-4 text-sm">
          <div class="grid gap-3 sm:grid-cols-2">
            <div class="rounded-xl bg-slate-50 p-3"><p class="text-xs text-slate-500">{{ t('license.plan') }}</p><p class="mt-1 font-bold text-slate-900">{{ status?.plan || '-' }}</p></div>
            <div class="rounded-xl bg-slate-50 p-3"><p class="text-xs text-slate-500">{{ isTrial ? t('license.trialExpires') : t('license.expires') }}</p><p class="mt-1 font-bold text-slate-900">{{ formatDate(expiresAt) }}</p></div>
            <div v-if="isTrial" class="rounded-xl bg-slate-50 p-3"><p class="text-xs text-slate-500">{{ t('license.trialStarted') }}</p><p class="mt-1 font-bold text-slate-900">{{ formatDate(status?.trial_started_at) }}</p></div>
            <div v-else class="rounded-xl bg-slate-50 p-3"><p class="text-xs text-slate-500">{{ t('license.licenseId') }}</p><p class="mt-1 break-all font-mono text-xs font-bold text-slate-900">{{ status?.license_id || '-' }}</p></div>
          </div>
          <div><p class="text-xs text-slate-500">{{ t('license.deviceHash') }}</p><div class="mt-1 flex items-center gap-2"><code class="min-w-0 flex-1 break-all rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700">{{ status?.device_hash }}</code><Button variant="outline" size="icon-sm" @click="copyDeviceHash"><Check v-if="copied" class="text-emerald-600" /><Copy v-else /></Button></div></div>
        </CardContent>
      </Card>
      <Card class="app-surface overflow-hidden border-none">
        <CardHeader class="border-b border-[#d8ebf7] bg-[#eaf7ff]"><CardTitle class="flex items-center gap-2"><KeyRound class="h-5 w-5 text-cyan-700" />{{ t('license.activateTitle') }}</CardTitle><CardDescription>{{ t('license.activateDescription') }}</CardDescription></CardHeader>
        <CardContent>
          <textarea v-model="code" rows="7" :placeholder="t('license.codePlaceholder')" class="w-full resize-y rounded-xl border border-slate-200 bg-slate-50 p-3 font-mono text-xs text-slate-900 outline-none transition focus:border-cyan-500 focus:bg-white focus:ring-2 focus:ring-cyan-500/15" />
          <p v-if="error" class="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
          <div class="mt-4 flex flex-wrap gap-2"><Button :disabled="activating || !code.trim()" @click="activate">{{ activating ? t('license.activating') : t('license.activate') }}</Button><Button variant="outline" @click="load"><RefreshCw class="h-4 w-4" />{{ t('common.refresh') }}</Button></div>
          <p class="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-500">{{ status?.entitled && isTrial ? t('license.emptyLicense') : t('license.codeNotStored') }}</p>
          <p class="mt-2 text-xs leading-5 text-slate-500">{{ t('license.securityHint') }}</p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
