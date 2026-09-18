<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLogs } from '@/composables/useLogs'
import { useTasks } from '@/composables/useTasks'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from '@/components/ui/toast'
import { diagnoseLogs, type LogDiagnosis } from '@/api/logs'
import { Activity, AlertTriangle, CheckCircle2, RefreshCw, Search, TerminalSquare, Trash2, XCircle } from 'lucide-vue-next'

const { t } = useI18n()
const { tasks } = useTasks()
const { logs, isAutoRefresh, clearLogs, toggleAutoRefresh, fetchLogs, setTaskId, loadLatest, loadPrevious, isFetchingHistory, hasMoreHistory } = useLogs()
const logContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
const isClearDialogOpen = ref(false)
const selectedTaskId = ref('')
const isPrepending = ref(false)
const lastScrollTop = ref(0)
const lastScrollHeight = ref(0)
const diagnosis = ref<LogDiagnosis | null>(null)
const isDiagnosing = ref(false)

// Auto-scroll logic
watch(logs, async () => {
  if (isPrepending.value) {
    await nextTick()
    if (logContainer.value) {
      const delta = logContainer.value.scrollHeight - lastScrollHeight.value
      logContainer.value.scrollTop = lastScrollTop.value + delta
    }
    isPrepending.value = false
    return
  }
  if (autoScroll.value) {
    await nextTick()
    scrollToBottom()
  }
})

watch(tasks, (list) => {
  if (!list.length) {
    selectedTaskId.value = ''
    setTaskId(null)
    return
  }
  if (selectedTaskId.value && list.some((task) => String(task.id) === selectedTaskId.value)) {
    return
  }
  const running = list.find((task) => task.is_running)
  const fallback = list[0]
  if (!fallback) {
    selectedTaskId.value = ''
    setTaskId(null)
    return
  }
  selectedTaskId.value = String(running ? running.id : fallback.id)
}, { immediate: true })

watch(selectedTaskId, (taskId) => {
  const resolvedTaskId = taskId ? Number(taskId) : null
  setTaskId(resolvedTaskId)
  if (resolvedTaskId) {
    loadLatest(50)
    diagnosis.value = null
  }
})

async function runDiagnosis() {
  if (!selectedTaskId.value) return
  isDiagnosing.value = true
  try {
    diagnosis.value = await diagnoseLogs(Number(selectedTaskId.value))
  } catch (e) {
    toast({ title: t('logs.diagnosisFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isDiagnosing.value = false
  }
}

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

async function handleScroll() {
  if (!logContainer.value) return
  if (!hasMoreHistory.value || isFetchingHistory.value) return
  if (logContainer.value.scrollTop > 120) return
  lastScrollTop.value = logContainer.value.scrollTop
  lastScrollHeight.value = logContainer.value.scrollHeight
  isPrepending.value = true
  await loadPrevious(50)
}

function openClearDialog() {
  isClearDialogOpen.value = true
}

async function handleClearLogs() {
  try {
    await clearLogs()
    toast({ title: t('logs.logsCleared') })
  } catch (e) {
    toast({
      title: t('logs.clearFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isClearDialogOpen.value = false
  }
}
</script>

<template>
  <div class="logs-page page-shell flex min-h-[calc(100dvh-120px)] flex-col gap-4 overflow-hidden rounded-[28px] p-1.5 sm:p-2">
    <div class="command-panel-dark overflow-hidden">
      <div class="border-b border-white/10 bg-slate-950 px-4 py-4 text-white sm:px-5">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div>
            <p class="eyebrow text-cyan-100/75">{{ t('logs.eyebrow') }}</p>
            <h1 class="mt-1 text-2xl font-black tracking-tight text-white sm:text-3xl">{{ t('logs.title') }}</h1>
          </div>
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Label class="text-sm font-medium text-white/65">{{ t('logs.task') }}</Label>
          <Select v-model="selectedTaskId">
            <SelectTrigger class="w-full sm:w-[260px]">
              <SelectValue :placeholder="t('logs.selectTask')" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="task in tasks" :key="task.id" :value="String(task.id)">
                {{ task.task_name }}{{ task.is_running ? t('logs.taskRunningSuffix') : '' }}
              </SelectItem>
            </SelectContent>
          </Select>
          </div>
        </div>
      
        <div class="flex flex-col gap-2 md:flex-row md:flex-wrap md:items-center md:justify-end">
        <Button variant="outline" size="sm" class="border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white" :disabled="!selectedTaskId" @click="fetchLogs">
          <RefreshCw class="mr-1.5 h-4 w-4" aria-hidden="true" />
          {{ t('common.refresh') }}
        </Button>

        <Button variant="outline" size="sm" class="border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white" :disabled="!selectedTaskId || isDiagnosing" @click="runDiagnosis">
          <Search class="mr-2 h-4 w-4" />
          {{ isDiagnosing ? t('logs.diagnosing') : t('logs.diagnose') }}
        </Button>

        <div class="flex items-center space-x-2">
          <Switch id="auto-refresh" :model-value="isAutoRefresh" @update:model-value="toggleAutoRefresh" />
          <Label for="auto-refresh" class="text-white/75">{{ t('logs.autoRefresh') }}</Label>
        </div>

        <div class="flex items-center space-x-2">
          <Switch id="auto-scroll" v-model="autoScroll" />
          <Label for="auto-scroll" class="text-white/75">{{ t('logs.autoScroll') }}</Label>
        </div>

        <Button variant="destructive" size="sm" :disabled="!selectedTaskId" @click="openClearDialog">
          <Trash2 class="mr-1.5 h-4 w-4" aria-hidden="true" />
          {{ t('logs.clearLogs') }}
        </Button>
        </div>
      </div>
      </div>
      <div class="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-white/10 px-4 py-3 text-xs text-white/55 sm:px-5">
        <span class="inline-flex items-center gap-1.5"><Activity class="h-3.5 w-3.5 text-[var(--brand-lime)]" aria-hidden="true" />{{ t('logs.streamHint') }}</span>
        <span>{{ t('logs.historyHint') }}</span>
      </div>
    </div>

    <Card v-if="diagnosis" class="app-surface border-none bg-[#fbfeff] shadow-[0_14px_34px_-28px_rgba(14,116,144,0.55)]">
      <CardContent class="p-4">
        <div class="flex items-start gap-3">
          <CheckCircle2 v-if="diagnosis.status === 'ok'" class="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
          <XCircle v-else-if="diagnosis.status === 'error'" class="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
          <AlertTriangle v-else class="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
          <div class="min-w-0">
            <p class="font-semibold text-slate-900">{{ diagnosis.title }}</p>
            <p class="mt-1 text-sm text-[#365773]">{{ diagnosis.summary }}</p>
            <p v-if="diagnosis.advice" class="mt-2 text-sm font-medium text-amber-700">{{ t('logs.advice', { value: diagnosis.advice }) }}</p>
          </div>
        </div>
        <div v-if="diagnosis.matches.length > 1" class="mt-4 flex flex-wrap gap-2">
          <span v-for="match in diagnosis.matches" :key="match.category" class="rounded-full border border-[#c8e3f3] bg-[#eaf7ff] px-3 py-1 text-xs font-medium text-[#365773]">{{ match.title }}</span>
        </div>
      </CardContent>
    </Card>

    <Card class="logs-console-shell flex min-h-[360px] flex-1 flex-col overflow-hidden border-none">
      <CardContent class="relative flex-1 p-0">
        <div class="pointer-events-none absolute left-4 top-4 z-10 inline-flex items-center gap-2 rounded-lg border border-cyan-200/20 bg-[#0b2541]/90 px-3 py-1.5 text-[11px] font-semibold text-cyan-100 backdrop-blur-sm">
          <TerminalSquare class="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
          {{ t('logs.consoleLabel') }}
        </div>
        <pre
          ref="logContainer"
          @scroll="handleScroll"
          class="absolute inset-0 overflow-auto bg-[#071426] p-4 pt-16 font-mono text-sm leading-6 text-sky-50 whitespace-pre-wrap break-all"
          aria-live="polite"
        >{{ logs || t('logs.empty') }}</pre>
      </CardContent>
    </Card>

    <Dialog v-model:open="isClearDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ t('logs.dialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ t('logs.dialogDescription') }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isClearDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" @click="handleClearLogs">{{ t('logs.confirmClear') }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
