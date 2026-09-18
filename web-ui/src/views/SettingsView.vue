<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSettings } from '@/composables/useSettings'
import type { NotificationSettingsUpdate, NotificationTestResponse, DiagnosticsResponse, LoginStateStatus, ReleaseInfo, BackupStatus } from '@/api/settings'
import { getDiagnostics, getLoginStateStatus, getBackupStatus, restoreBackup, downloadDiagnosticBundle, downloadFullBackup, getReleaseInfo } from '@/api/settings'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from '@/components/ui/toast'
import { CheckCircle2, AlertTriangle, ArrowRight, Sparkles } from 'lucide-vue-next'
import { formatDateTime } from '@/i18n'
import { getPromptContent, listPrompts, updatePrompt } from '@/api/prompts'
import NotificationSettingsPanel from '@/components/settings/NotificationSettingsPanel.vue'
import RotationSettingsPanel from '@/components/settings/RotationSettingsPanel.vue'
const { t } = useI18n()
const router = useRouter()

const {
  notificationSettings,
  aiSettings,
  rotationSettings,
  systemStatus,
  isLoading,
  isSaving,
  isReady,
  error,
  refreshStatus,
  saveNotificationSettings,
  testNotification,
  saveAiSettings,
  saveRotationSettings,
  testAiConnection
} = useSettings()

const activeTab = ref('ai')
const route = useRoute()
const validTabs = new Set(['notifications', 'ai', 'rotation', 'status', 'prompts'])

const promptFiles = ref<string[]>([])
const selectedPrompt = ref<string | null>(null)
const promptContent = ref('')
const isPromptLoading = ref(false)
const isPromptSaving = ref(false)
const promptError = ref<string | null>(null)
const diagnostics = ref<DiagnosticsResponse | null>(null)
const isDiagnosing = ref(false)
const setupCompleted = ref(localStorage.getItem('setupWizardCompleted') === 'true')
const loginStateStatus = ref<LoginStateStatus | null>(null)
const backupStatus = ref<BackupStatus | null>(null)
const backupInput = ref<HTMLInputElement | null>(null)
const isBackupWorking = ref(false)
const releaseInfo = ref<ReleaseInfo | null>(null)

async function runDiagnostics() {
  isDiagnosing.value = true
  try {
    diagnostics.value = await getDiagnostics()
  } catch (e) {
    notifyError(t('settings.status.diagnosisFailed'), (e as Error).message)
  } finally {
    isDiagnosing.value = false
  }
}

async function refreshLocalProtection() {
  try {
    const [login, backup] = await Promise.all([getLoginStateStatus(), getBackupStatus()])
    loginStateStatus.value = login
    backupStatus.value = backup
  } catch (e) {
    notifyError(t('settings.status.localStateFailed'), (e as Error).message)
  }
}

async function loadReleaseInfo() {
  try {
    releaseInfo.value = await getReleaseInfo()
  } catch (e) {
    notifyError(t('settings.status.releaseFailed'), (e as Error).message)
  }
}

function downloadBackup() {
  window.location.href = '/api/backup/download'
}

function downloadMigrationBackup() {
  if (!window.confirm(t('settings.status.fullBackupConfirm'))) return
  downloadFullBackup()
}

function chooseBackup() {
  backupInput.value?.click()
}

async function handleBackupSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.zip')) {
    notifyError(t('settings.status.restoreFailed'), t('settings.status.zipOnly'))
    return
  }
  if (!window.confirm(t('settings.status.restoreConfirm'))) return
  isBackupWorking.value = true
  try {
    const result = await restoreBackup(file)
    const restartNote = result.restart_recommended ? t('settings.status.restartRecommended') : ''
    notifySuccess(t('settings.status.restoreSuccess'), `${t('settings.status.safetyBackup', { value: result.safety_backup })} ${restartNote}`.trim())
    await refreshLocalProtection()
  } catch (e) {
    notifyError(t('settings.status.restoreFailed'), (e as Error).message)
  } finally {
    isBackupWorking.value = false
  }
}

function completeSetup() {
  setupCompleted.value = true
  localStorage.setItem('setupWizardCompleted', 'true')
  notifySuccess(t('settings.wizard.completedTitle'), t('settings.wizard.completedDescription'))
}

function reopenSetupWizard() {
  router.push({ query: { ...route.query, wizard: '1' } })
}

function notifySuccess(title: string, description?: string) {
  toast({ title, description })
}

function notifyError(title: string, description?: string) {
  toast({ title, description, variant: 'destructive' })
}

async function handleSaveNotifications(payload: NotificationSettingsUpdate) {
  try {
    await saveNotificationSettings(payload)
    notifySuccess(t('settings.notifications.saved'))
  } catch (e) {
    notifyError(t('settings.notifications.saveFailed'), (e as Error).message)
  }
}

async function handleTestNotification(payload: {
  channel?: string
  settings: NotificationSettingsUpdate
}): Promise<NotificationTestResponse> {
  try {
    const result = await testNotification(payload)
    return result
  } catch (e) {
    notifyError(t('settings.notifications.testFailed'), (e as Error).message)
    throw e
  }
}

async function handleSaveAi() {
  try {
    await saveAiSettings()
    notifySuccess(t('settings.ai.saved'))
  } catch (e) {
    notifyError(t('settings.ai.saveFailed'), (e as Error).message)
  }
}

async function handleSaveRotation() {
  try {
    await saveRotationSettings()
    notifySuccess(t('settings.rotation.saved'))
  } catch (e) {
    notifyError(t('settings.rotation.saveFailed'), (e as Error).message)
  }
}

async function handleTestAi() {
  try {
    const res = await testAiConnection()
    notifySuccess(t('settings.ai.testSuccess'), res.message)
  } catch (e) {
    notifyError(t('settings.ai.testFailed'), (e as Error).message)
  }
}

async function fetchPrompts() {
  isPromptLoading.value = true
  promptError.value = null
  try {
    const files = await listPrompts()
    promptFiles.value = files

    if (selectedPrompt.value && files.includes(selectedPrompt.value)) {
      return
    }

    const lastSelected = localStorage.getItem('lastSelectedPrompt')
    if (lastSelected && files.includes(lastSelected)) {
      selectedPrompt.value = lastSelected
      return
    }

    selectedPrompt.value = files[0] || null
  } catch (e) {
    promptError.value = (e as Error).message || t('settings.prompts.promptListFailed')
  } finally {
    isPromptLoading.value = false
  }
}

async function handleSavePrompt() {
  if (!selectedPrompt.value) {
    notifyError(t('settings.prompts.selectPromptFile'))
    return
  }
  isPromptSaving.value = true
  try {
    const res = await updatePrompt(selectedPrompt.value, promptContent.value)
    notifySuccess(t('settings.prompts.saveSuccess'), res.message)
  } catch (e) {
    notifyError(t('settings.prompts.saveFailed'), (e as Error).message)
  } finally {
    isPromptSaving.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'prompts') {
    fetchPrompts()
  }
  if (tab === 'status') {
    refreshLocalProtection()
    loadReleaseInfo()
  }
})

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === 'string' && validTabs.has(tab)) {
      activeTab.value = tab
    }
  },
  { immediate: true }
)

watch(selectedPrompt, async (value) => {
  if (!value) {
    promptContent.value = ''
    return
  }
  localStorage.setItem('lastSelectedPrompt', value)
  isPromptLoading.value = true
  promptError.value = null
  try {
    const data = await getPromptContent(value)
    promptContent.value = data.content
  } catch (e) {
    promptError.value = (e as Error).message || t('settings.prompts.promptContentFailed')
  } finally {
    isPromptLoading.value = false
  }
})
</script>

<template>
  <div class="settings-page page-shell relative space-y-5 overflow-hidden rounded-[28px] p-1.5 sm:p-2">
    <div class="command-hero flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
      <div>
        <p class="eyebrow text-[var(--brand-lime)]">{{ t('settings.eyebrow') }}</p>
        <h1 class="mt-1 text-2xl font-black tracking-tight text-white sm:text-3xl">{{ t('settings.title') }}</h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-white/65">{{ t('settings.description') }}</p>
      </div>
      <Button variant="outline" size="sm" class="border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white" @click="reopenSetupWizard">{{ t('settings.reopenWizard') }}</Button>
    </div>
    
    <div v-if="error" class="app-alert-error mb-4" role="alert">
      {{ error.message }}
    </div>

    <Card v-if="!setupCompleted" class="app-surface mb-6 overflow-hidden border-amber-200 bg-gradient-to-r from-amber-50 via-white to-[#eef8fd]">
      <CardHeader class="settings-card-header">
        <div class="flex items-start justify-between gap-4">
          <div>
            <CardTitle class="flex items-center gap-2"><Sparkles class="h-5 w-5 text-amber-500" />{{ t('settings.wizard.title') }}</CardTitle>
            <CardDescription class="mt-1">{{ t('settings.wizard.description') }}</CardDescription>
          </div>
          <Button variant="ghost" size="sm" @click="completeSetup">{{ t('settings.wizard.skip') }}</Button>
        </div>
      </CardHeader>
      <CardContent class="settings-card-content grid gap-4 md:grid-cols-3">
        <div class="rounded-xl border border-white/80 bg-white/75 p-4 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-wider text-[#23789a]">01</p>
          <p class="mt-2 font-bold text-[#163b57]">{{ t('settings.wizard.stepAi') }}</p>
          <p class="mt-1 text-sm text-[#52738b]">{{ t('settings.wizard.stepAiDescription') }}</p>
          <Button variant="link" class="mt-2 h-auto px-0" @click="activeTab = 'ai'">{{ t('settings.wizard.goConfigure') }} <ArrowRight class="ml-1 h-3 w-3" /></Button>
        </div>
        <div class="rounded-xl border border-white/80 bg-white/75 p-4 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-wider text-[#23789a]">02</p>
          <p class="mt-2 font-bold text-[#163b57]">{{ t('settings.wizard.stepLogin') }}</p>
          <p class="mt-1 text-sm text-[#52738b]">{{ t('settings.wizard.stepLoginDescription') }}</p>
          <Button variant="link" class="mt-2 h-auto px-0" @click="activeTab = 'status'">{{ t('settings.wizard.checkStatus') }} <ArrowRight class="ml-1 h-3 w-3" /></Button>
        </div>
        <div class="rounded-xl border border-white/80 bg-white/75 p-4 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-wider text-[#23789a]">03</p>
          <p class="mt-2 font-bold text-[#163b57]">{{ t('settings.wizard.stepDiagnostics') }}</p>
          <p class="mt-1 text-sm text-[#52738b]">{{ t('settings.wizard.stepDiagnosticsDescription') }}</p>
          <Button variant="link" class="mt-2 h-auto px-0" @click="activeTab = 'status'; runDiagnostics()">{{ t('settings.wizard.runDiagnostics') }} <ArrowRight class="ml-1 h-3 w-3" /></Button>
        </div>
      </CardContent>
      <CardFooter class="settings-card-footer">
        <Button @click="completeSetup">{{ t('settings.wizard.complete') }}</Button>
      </CardFooter>
    </Card>

    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="settings-tab-list mb-5 flex w-full flex-nowrap justify-start overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
        <TabsTrigger class="settings-tab-trigger shrink-0" value="ai">{{ t('settings.tabs.ai') }}</TabsTrigger>
        <TabsTrigger class="settings-tab-trigger shrink-0" value="rotation">{{ t('settings.tabs.rotation') }}</TabsTrigger>
        <TabsTrigger class="settings-tab-trigger shrink-0" value="notifications">{{ t('settings.tabs.notifications') }}</TabsTrigger>
        <TabsTrigger class="settings-tab-trigger shrink-0" value="status">{{ t('settings.tabs.status') }}</TabsTrigger>
        <TabsTrigger class="settings-tab-trigger shrink-0" value="prompts">{{ t('settings.tabs.prompts') }}</TabsTrigger>
      </TabsList>

      <!-- AI Tab -->
      <TabsContent value="ai">
        <Card class="app-surface overflow-hidden border-none">
          <CardHeader class="settings-card-header flex-col border-b border-[#d8ebf7] bg-[#eaf7ff] sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>{{ t('settings.ai.title') }}</CardTitle>
            <CardDescription>{{ t('settings.ai.description') }}</CardDescription>
          </CardHeader>
          <CardContent v-if="isReady" class="settings-card-content settings-form-content">
            <div class="settings-field">
              <Label>{{ t('settings.ai.baseUrl') }}</Label>
              <Input v-model="aiSettings.OPENAI_BASE_URL" class="settings-input" placeholder="https://api.openai.com/v1" />
            </div>
            <div class="settings-field">
              <Label>{{ t('settings.ai.apiKey') }}</Label>
              <Input
                v-model="aiSettings.OPENAI_API_KEY"
                class="settings-input"
                type="password"
                :placeholder="t('settings.ai.keyPlaceholder')"
              />
              <p class="settings-helper text-xs text-[#52738b]">
                {{ systemStatus?.env_file.openai_api_key_set ? t('settings.ai.keyConfigured') : t('settings.ai.keyMissing') }}
              </p>
            </div>
            <div class="settings-field">
              <Label>{{ t('settings.ai.modelName') }}</Label>
              <Input v-model="aiSettings.OPENAI_MODEL_NAME" class="settings-input" placeholder="gpt-3.5-turbo" />
            </div>
            <div class="settings-field">
              <Label>{{ t('settings.ai.proxy') }}</Label>
              <Input v-model="aiSettings.PROXY_URL" class="settings-input" placeholder="http://127.0.0.1:7890" />
            </div>
          </CardContent>
          <CardContent v-else class="py-8 text-sm text-[#52738b]">
            {{ t('settings.ai.loading') }}
          </CardContent>
          <CardFooter v-if="isReady" class="settings-card-footer flex flex-wrap">
            <Button variant="outline" @click="handleTestAi" :disabled="isSaving">{{ t('settings.ai.testConnection') }}</Button>
            <Button @click="handleSaveAi" :disabled="isSaving">{{ t('settings.ai.save') }}</Button>
          </CardFooter>
        </Card>
      </TabsContent>

      <!-- Rotation Tab -->
      <TabsContent value="rotation">
        <RotationSettingsPanel
          :settings="rotationSettings"
          :is-ready="isReady"
          :is-saving="isSaving"
          @save="handleSaveRotation"
        />
      </TabsContent>

      <!-- Notifications Tab -->
      <TabsContent value="notifications">
        <NotificationSettingsPanel
          :settings="notificationSettings"
          :is-ready="isReady"
          :is-saving="isSaving"
          :save-settings="handleSaveNotifications"
          :test-settings="handleTestNotification"
        />
      </TabsContent>

      <!-- Status Tab -->
      <TabsContent value="status">
        <Card class="app-surface overflow-hidden border-none">
          <CardHeader class="settings-card-header border-b border-[#d8ebf7] bg-[#eaf7ff]">
            <CardTitle>{{ t('settings.status.title') }}</CardTitle>
            <div class="flex justify-end">
                <Button variant="outline" size="sm" @click="refreshStatus" :disabled="isLoading">{{ t('settings.status.refresh') }}</Button>
            </div>
          </CardHeader>
          <CardContent class="settings-card-content">
            <div v-if="systemStatus" class="space-y-6">
              <!-- Scraper Process Status -->
                <div class="app-surface-subtle flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 class="font-medium">{{ t('settings.status.scraper') }}</h3>
                        <p class="text-sm text-[#52738b]">{{ t('settings.status.scraperDescription') }}</p>
                </div>
                <span class="status-pill" :class="systemStatus.scraper_running ? 'status-pill-success' : 'status-pill-muted'">
                  {{ systemStatus.scraper_running ? t('common.running') : t('common.idle') }}
                </span>
              </div>

              <!-- Env Config Status -->
              <div>
                <div class="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h3 class="font-medium">{{ t('settings.status.env') }}</h3>
                        <p class="text-sm text-[#52738b]">{{ t('settings.status.envDescription') }}</p>
                    </div>
                    <span class="status-pill" :class="systemStatus.env_file.exists ? 'status-pill-success' : 'status-pill-danger'">
                        {{ systemStatus.env_file.exists ? t('settings.status.loaded') : t('settings.status.missing') }}
                    </span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="app-surface-subtle p-4" :class="systemStatus.env_file.openai_api_key_set ? 'border-emerald-200 bg-emerald-50/60' : 'border-amber-200 bg-amber-50/60'">
                        <div class="flex justify-between items-center">
                            <span class="text-sm font-semibold text-slate-800">{{ t('settings.ai.apiKey') }}</span>
                            <span class="status-pill" :class="systemStatus.env_file.openai_api_key_set ? 'status-pill-success' : 'status-pill-warning'">
                                {{ systemStatus.env_file.openai_api_key_set ? t('common.active') : t('common.inactive') }}
                            </span>
                        </div>
                    </div>
                    
                    <div class="app-surface-subtle p-4" :class="systemStatus.configured_notification_channels?.length ? 'border-emerald-200 bg-emerald-50/60' : 'border-[#c8e3f3] bg-[#eef8fd]'">
                         <div class="flex justify-between items-center">
                            <span class="text-sm font-semibold text-slate-800">{{ t('settings.status.channels') }}</span>
                             <span class="status-pill" :class="systemStatus.configured_notification_channels?.length ? 'status-pill-success' : 'status-pill-muted'">
                                {{ systemStatus.configured_notification_channels?.length ? t('common.active') : t('common.inactive') }}
                            </span>
                        </div>
                         <div class="mt-2 text-xs text-[#52738b]">
                            {{ systemStatus.configured_notification_channels?.join(', ') || t('settings.status.none') }}
                        </div>
                    </div>
                </div>
              </div>
            </div>
            <div v-else class="py-10 text-center text-sm text-[#52738b]">
                {{ t('settings.status.fetching') }}
            </div>
          </CardContent>
        </Card>

        <Card class="app-surface mt-6 overflow-hidden border-none">
          <CardHeader class="settings-card-header border-b border-[#d8ebf7] bg-[#eaf7ff]">
            <div class="flex items-center justify-between gap-4">
              <div>
                <CardTitle>{{ t('settings.status.diagnosticsTitle') }}</CardTitle>
                <CardDescription>{{ t('settings.status.diagnosticsDescription') }}</CardDescription>
              </div>
              <Button variant="outline" size="sm" @click="runDiagnostics" :disabled="isDiagnosing">
                {{ isDiagnosing ? t('settings.status.diagnosing') : t('settings.status.runDiagnostics') }}
              </Button>
            </div>
          </CardHeader>
          <CardContent class="settings-card-content">
            <div v-if="diagnostics" class="space-y-3">
              <div class="rounded-lg border p-3 text-sm" :class="diagnostics.success ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-amber-200 bg-amber-50 text-amber-800'">
                {{ diagnostics.summary }}
              </div>
              <div v-for="check in diagnostics.checks" :key="check.key" class="flex items-start gap-3 rounded-lg border border-[#d8ebf7] bg-[#fbfeff] p-3">
                <CheckCircle2 v-if="check.status === 'pass'" class="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                <AlertTriangle v-else class="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                <div>
                  <p class="font-medium text-slate-800">{{ check.label }}</p>
                  <p class="text-sm text-[#52738b]">{{ check.detail }}</p>
                </div>
              </div>
            </div>
            <p v-else class="text-sm text-[#52738b]">{{ t('settings.status.diagnosticEmpty') }}</p>
          </CardContent>
        </Card>

        <Card v-if="releaseInfo" class="app-surface mt-6 overflow-hidden border-none">
          <CardHeader class="settings-card-header border-b border-[#d8ebf7] bg-[#eaf7ff]">
            <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>{{ t('settings.status.releaseTitle') }}</CardTitle>
                <CardDescription>{{ t('settings.status.releaseDescription') }}</CardDescription>
              </div>
              <span class="w-fit rounded-full border border-[#b9dced] bg-[#eef8fd] px-3 py-1 text-xs font-bold text-[#365773]">
                {{ releaseInfo.version }} · {{ releaseInfo.build_type }}
              </span>
            </div>
          </CardHeader>
          <CardContent class="settings-card-content grid gap-6 md:grid-cols-3">
            <div>
              <p class="eyebrow">{{ t('settings.status.releaseNotes') }}</p>
              <ul class="mt-2 space-y-2 text-sm text-[#365773]">
                <li v-for="item in releaseInfo.release_notes" :key="item" class="flex gap-2">
                  <CheckCircle2 class="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                  <span>{{ item }}</span>
                </li>
              </ul>
            </div>
            <div>
              <p class="eyebrow">{{ t('settings.status.supportItems') }}</p>
              <ul class="mt-2 space-y-2 text-sm text-[#365773]">
                <li v-for="item in releaseInfo.support_items" :key="item" class="flex gap-2">
                  <CheckCircle2 class="mt-0.5 h-4 w-4 shrink-0 text-sky-600" />
                  <span>{{ item }}</span>
                </li>
              </ul>
            </div>
            <div>
              <p class="eyebrow">{{ t('settings.status.supportSteps') }}</p>
              <ol class="mt-2 space-y-2 text-sm text-[#365773]">
                <li v-for="(item, index) in releaseInfo.support_steps" :key="item" class="flex gap-2">
                  <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-100 text-[11px] font-bold text-amber-700">{{ index + 1 }}</span>
                  <span>{{ item }}</span>
                </li>
              </ol>
            </div>
          </CardContent>
        </Card>

        <Card class="app-surface mt-6 overflow-hidden border-none">
          <CardHeader class="settings-card-header border-b border-[#d8ebf7] bg-[#eaf7ff]">
            <CardTitle>{{ t('settings.status.protectionTitle') }}</CardTitle>
            <CardDescription>{{ t('settings.status.protectionDescription') }}</CardDescription>
          </CardHeader>
          <CardContent class="settings-card-content space-y-5">
            <div class="flex flex-col items-start justify-between gap-4 rounded-xl border p-5 sm:flex-row" :class="loginStateStatus?.exists && loginStateStatus.valid_json ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'">
              <div>
                <p class="font-semibold text-slate-800">{{ t('settings.status.loginState') }}</p>
                <p class="mt-1 text-sm text-[#365773]">{{ loginStateStatus?.message || t('settings.status.refreshLocalHint') }}</p>
                <p v-if="loginStateStatus?.updated_at" class="mt-1 text-xs text-[#52738b]">{{ t('settings.status.lastUpdated', { value: formatDateTime(new Date(loginStateStatus.updated_at * 1000), { dateStyle: 'medium', timeStyle: 'short' }) }) }}</p>
              </div>
              <Button variant="outline" size="sm" class="shrink-0" @click="refreshLocalProtection">{{ t('settings.status.refreshLocalState') }}</Button>
            </div>
            <div class="rounded-xl border border-[#c8e3f3] bg-[#eef8fd] p-4">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p class="font-semibold text-slate-800">{{ t('settings.status.backupTitle') }}</p>
                  <p class="mt-1 text-sm text-[#52738b]">{{ t('settings.status.backupDescription') }}</p>
                  <p v-if="backupStatus" class="mt-1 text-xs text-[#6c879d]">{{ t('settings.status.backupSize', { value: (backupStatus.total_bytes / 1024 / 1024).toFixed(1) }) }}</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <Button variant="outline" @click="downloadBackup">{{ t('settings.status.downloadBackup') }}</Button>
                  <Button variant="ghost" @click="downloadMigrationBackup">{{ t('settings.status.downloadFullBackup') }}</Button>
                  <Button variant="secondary" :disabled="isBackupWorking" @click="chooseBackup">{{ t('settings.status.restoreBackup') }}</Button>
                  <input ref="backupInput" type="file" accept=".zip,application/zip" class="hidden" @change="handleBackupSelected" />
                </div>
              </div>
            </div>
            <div class="rounded-xl border border-sky-100 bg-sky-50 p-4">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p class="font-semibold text-slate-800">{{ t('settings.status.diagnosticBundleTitle') }}</p>
                  <p class="mt-1 text-sm text-[#365773]">{{ t('settings.status.diagnosticBundleDescription') }}</p>
                </div>
                <Button variant="outline" @click="downloadDiagnosticBundle">{{ t('settings.status.downloadDiagnosticBundle') }}</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Prompt Tab -->
      <TabsContent value="prompts">
        <Card class="app-surface overflow-hidden border-none">
          <CardHeader class="settings-card-header border-b border-[#d8ebf7] bg-[#eaf7ff]">
            <CardTitle>{{ t('settings.prompts.title') }}</CardTitle>
            <CardDescription>{{ t('settings.prompts.description') }}</CardDescription>
          </CardHeader>
          <CardContent class="settings-card-content space-y-6">
            <div v-if="promptError" class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded">
              {{ promptError }}
            </div>

            <div class="settings-field">
              <Label>{{ t('settings.prompts.selectFile') }}</Label>
              <Select
                :model-value="selectedPrompt || undefined"
                @update:model-value="(value) => selectedPrompt = value as string"
              >
                <SelectTrigger>
                  <SelectValue :placeholder="t('settings.prompts.placeholder')" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="file in promptFiles" :key="file" :value="file">
                    {{ file }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <p v-if="!promptFiles.length && !isPromptLoading" class="text-sm text-[#52738b]">
                {{ t('settings.prompts.none') }}
              </p>
            </div>

            <div class="settings-field">
              <Label>{{ t('settings.prompts.content') }}</Label>
              <Textarea
                v-model="promptContent"
                class="min-h-[240px]"
                :disabled="!selectedPrompt || isPromptLoading"
                :placeholder="t('settings.prompts.contentPlaceholder')"
              />
            </div>
          </CardContent>
          <CardFooter class="settings-card-footer">
            <Button :disabled="isPromptSaving || !selectedPrompt" @click="handleSavePrompt">
              {{ isPromptSaving ? t('common.saving') : t('settings.prompts.save') }}
            </Button>
          </CardFooter>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>
