<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Task } from '@/types/task.d.ts'
import type { TaskHistory } from '@/api/tasks'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { 
  Play, 
  Square, 
  Pencil, 
  Trash2, 
  User, 
  BrainCircuit, 
  Keyboard,
  Clock,
  Layers,
  MapPin,
  RefreshCcw,
  Search,
  Eye,
} from 'lucide-vue-next'
import { formatCountdown, formatNextRunAbsolute } from '@/lib/taskSchedule'

interface Props {
  tasks: Task[]
  isLoading: boolean
  stoppingIds?: Set<number>
  histories?: Record<number, TaskHistory>
  emptyMessage?: string
}

const props = defineProps<Props>()
const { t } = useI18n()
const isStopping = (id: number) => props.stoppingIds?.has(id) ?? false
const historyFor = (task: Task) => props.histories?.[task.id]
const isKeywordMode = (task: Task) => task.decision_mode === 'keyword'
const nowMs = ref(Date.now())
let timer: number | null = null

onMounted(() => {
  timer = window.setInterval(() => {
    nowMs.value = Date.now()
  }, 1000)
})

onBeforeUnmount(() => {
  if (timer !== null) {
    window.clearInterval(timer)
  }
})

const resolveAccountStrategyLabel = (task: Task) => {
  if (task.account_strategy === 'rotate') return t('tasks.table.accountRotate')
  if (task.account_strategy === 'fixed') return t('tasks.table.accountFixed')
  return t('tasks.table.accountAuto')
}

const resolveAccountName = (task: Task) => {
  if (!task.account_state_file) return t('tasks.table.systemSelected')
  const segments = task.account_state_file.split('/')
  const filename = segments[segments.length - 1] || task.account_state_file
  return filename.replace('.json', '')
}

const resolveCountdownText = (task: Task) => {
  if (!task.cron) return t('tasks.table.manualTrigger')
  if (!task.enabled) return t('tasks.table.disabled')
  return formatCountdown(task.next_run_at, nowMs.value) || t('tasks.table.waitingSchedule')
}

const resolveCountdownTone = (task: Task) => {
  if (!task.cron) return 'text-[#52738b]'
  if (!task.enabled) return 'text-[#52738b]'
  return 'text-[#b45309]'
}

const resolveNextRunLabel = (task: Task) => {
  if (!task.cron || !task.enabled || !task.next_run_at) return null
  return formatNextRunAbsolute(task.next_run_at)
}

const emit = defineEmits<{
  (e: 'delete-task', taskId: number): void
  (e: 'run-task', taskId: number): void
  (e: 'stop-task', taskId: number): void
  (e: 'edit-task', task: Task): void
  (e: 'refresh-criteria', task: Task): void
  (e: 'toggle-enabled', task: Task, enabled: boolean): void
  (e: 'view-results', task: Task): void
}>()
</script>

<template>
  <div class="task-table-shell">
    <div class="space-y-4 p-4 lg:hidden">
      <template v-if="isLoading && tasks.length === 0">
        <div class="flex min-h-40 flex-col items-center justify-center gap-2 text-[#2b6684]">
          <RefreshCcw class="h-6 w-6 animate-spin text-[#0e7490]" />
          <span class="text-sm font-medium italic">{{ t('tasks.table.syncing') }}</span>
        </div>
      </template>
      <template v-else-if="tasks.length === 0">
        <div class="flex min-h-40 flex-col items-center justify-center gap-2 text-[#4c7d98]">
          <Layers class="h-12 w-12 opacity-[0.45]" />
          <p class="text-sm font-bold">{{ emptyMessage || t('tasks.table.empty') }}</p>
        </div>
      </template>
      <template v-else>
        <article
          v-for="task in tasks"
          :key="task.id"
          class="rounded-xl border border-[#c8e3f3] bg-white p-4 shadow-[0_10px_24px_-20px_rgba(14,116,144,0.8)] transition-[border-color,box-shadow] hover:border-cyan-300 hover:shadow-md"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 space-y-2">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="truncate text-base font-black tracking-tight text-slate-900">
                  {{ task.task_name }}
                </h3>
                <Badge
                  variant="outline"
                  :class="[
                    'border-none px-2 py-0.5 text-[10px] font-black',
                    isKeywordMode(task) ? 'bg-blue-50 text-blue-600' : 'bg-emerald-50 text-emerald-600',
                  ]"
                >
                  <component :is="isKeywordMode(task) ? Keyboard : BrainCircuit" class="mr-1 h-3 w-3" />
                  {{ isKeywordMode(task) ? t('tasks.table.keywordMode') : t('tasks.table.aiMode') }}
                </Badge>
              </div>

              <div class="flex flex-wrap items-center gap-2 text-sm text-[#365773]">
                <div class="inline-flex items-center gap-1.5 rounded-md border border-[#c6e2f0] bg-[#f0f9fd] px-2 py-1 font-semibold">
                  <Search class="h-3.5 w-3.5 text-[#23789a]" />
                  {{ task.keyword }}
                </div>
                <span v-if="task.description" class="line-clamp-1 text-[#52738b]">
                  {{ task.description }}
                </span>
              </div>
            </div>

            <div class="flex flex-col items-end gap-2">
              <Switch
                :model-value="task.enabled"
                class="data-[state=checked]:bg-primary"
                @update:model-value="(val: boolean) => emit('toggle-enabled', task, val)"
              />
              <Badge
                variant="outline"
                :class="task.is_running ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-[#b9dced] bg-[#eef8fd] text-[#365773]'"
              >
                {{ task.is_running ? t('common.running') : t('common.idle') }}
              </Badge>
            </div>
          </div>

          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <div class="rounded-lg border border-[#d8ebf7] bg-[#fbfeff] p-3">
              <p class="text-[11px] font-bold uppercase tracking-[0.14em] text-[#365773]">
                {{ t('tasks.table.headers.crawl') }}
              </p>
              <p class="mt-2 text-sm font-bold text-[#163b57]">
                  ¥{{ task.min_price || 0 }} - {{ task.max_price || t('tasks.table.noUpperLimit') }}
              </p>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <Badge variant="outline" class="border-[#c6e2f0] bg-[#f0f9fd] text-[#365773]">
                  {{ task.personal_only ? t('tasks.table.personalOnly') : t('common.all') }}
                </Badge>
                <Badge variant="outline" class="border-[#c6e2f0] bg-[#f0f9fd] text-[#365773]">
                  {{ task.free_shipping ? t('tasks.table.freeShipping') : t('common.all') }}
                </Badge>
                <Badge v-if="task.region" variant="outline" class="border-[#c6e2f0] bg-[#f0f9fd] text-[#365773]">
                  <MapPin class="mr-1 h-3 w-3" />
                  {{ task.region }}
                </Badge>
              </div>
            </div>

            <div class="rounded-xl border border-[#d8ebf7] bg-[#fbfeff] p-3">
                <p class="text-[11px] font-bold uppercase tracking-[0.14em] text-[#365773]">
                {{ t('tasks.table.headers.schedule') }}
              </p>
              <p class="mt-2 text-sm font-bold" :class="resolveCountdownTone(task)">
                {{ resolveCountdownText(task) }}
              </p>
              <p v-if="resolveNextRunLabel(task)" class="mt-1 text-xs text-[#52738b]">
                {{ resolveNextRunLabel(task) }}
              </p>
              <div class="mt-2 flex flex-wrap items-center gap-2 text-xs font-semibold text-[#365773]">
                <span class="inline-flex items-center gap-1">
                  <Clock class="h-3.5 w-3.5" />
                  {{ task.cron || t('tasks.table.manualRun') }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <Layers class="h-3.5 w-3.5" />
                  {{ t('tasks.table.pages', { count: task.max_pages || 3 }) }}
                </span>
              </div>
            </div>

            <div class="rounded-lg border border-[#d8ebf7] bg-[#fbfeff] p-3 sm:col-span-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p class="text-[11px] font-bold uppercase tracking-[0.14em] text-[#365773]">
                    {{ t('tasks.table.headers.mode') }}
                  </p>
                  <p class="mt-2 text-sm font-semibold text-[#163b57]">
                    {{ resolveAccountStrategyLabel(task) }} · {{ resolveAccountName(task) }}
                  </p>
                </div>

                <div v-if="isKeywordMode(task)" class="rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700">
                  {{ t('tasks.table.keywordStrategies', { count: task.keyword_rules?.length || 0 }) }}
                </div>
                <div v-else class="flex flex-wrap items-center gap-2">
                  <div class="rounded-md border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs font-mono font-semibold text-emerald-700">
                    {{ t('tasks.table.criteriaConfigured') }}
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    class="text-emerald-700 hover:bg-emerald-50"
                    :aria-label="`${t('tasks.table.refreshCriteria')} ${task.task_name}`"
                    @click="emit('refresh-criteria', task)"
                  >
                    <RefreshCcw class="mr-1 h-3.5 w-3.5" />
                    {{ t('tasks.table.refreshCriteria') }}
                  </Button>
                </div>
              </div>
            </div>

            <div class="rounded-lg border border-[#b9dced] bg-[#edf8fd] p-3 sm:col-span-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                  <p class="text-[11px] font-bold uppercase tracking-[0.14em] text-[#365773]">{{ t('tasks.table.history') }}</p>
                <span v-if="historyFor(task)?.running" class="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                  <span class="size-1.5 animate-pulse rounded-full bg-emerald-500" />{{ t('tasks.table.runningNow') }}
                </span>
              </div>
              <div v-if="historyFor(task)" class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
                <span class="font-semibold text-[#163b57]">{{ t('tasks.table.runCount', { count: historyFor(task)?.total_runs || 0 }) }}</span>
                <span class="text-emerald-700">{{ t('tasks.table.successCount', { count: historyFor(task)?.success_count || 0 }) }}</span>
                <span :class="(historyFor(task)?.failure_count || 0) > 0 ? 'font-semibold text-rose-700' : 'text-[#52738b]'">{{ t('tasks.table.failureCount', { count: historyFor(task)?.failure_count || 0 }) }}</span>
              </div>
              <p v-else class="mt-2 text-xs font-medium text-[#52738b]">{{ t('tasks.table.noRuns') }}</p>
            </div>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              class="min-w-[120px] flex-1 border-cyan-200 text-cyan-700 hover:bg-cyan-50"
              :aria-label="`${t('tasks.console.results')} ${task.task_name}`"
              @click="emit('view-results', task)"
            >
              <Eye class="mr-1 h-3.5 w-3.5" />
              {{ t('tasks.console.results') }}
            </Button>
            <Button
              v-if="!task.is_running"
              size="sm"
              class="flex-1 min-w-[120px]"
              :class="task.enabled ? '' : 'pointer-events-none opacity-50'"
              :aria-label="`${t('tasks.table.start')} ${task.task_name}`"
              @click="emit('run-task', task.id)"
            >
              <Play class="mr-1 h-3.5 w-3.5 fill-current" />
              {{ t('tasks.table.start') }}
            </Button>
            <Button
              v-else
              size="sm"
              variant="destructive"
              class="flex-1 min-w-[120px]"
              :disabled="isStopping(task.id)"
              :aria-label="`${t('tasks.table.stop')} ${task.task_name}`"
              @click="emit('stop-task', task.id)"
            >
              <Square v-if="!isStopping(task.id)" class="mr-1 h-3.5 w-3.5 fill-current" />
              <RefreshCcw v-else class="mr-1 h-3.5 w-3.5 animate-spin" />
              {{ isStopping(task.id) ? t('tasks.table.stopping') : t('tasks.table.stop') }}
            </Button>
            <Button
              size="icon"
              variant="outline"
              class="size-10"
              :aria-label="`${t('common.edit')} ${task.task_name}`"
              @click="emit('edit-task', task)"
            >
              <Pencil class="h-4 w-4" />
            </Button>
            <Button
              size="icon"
              variant="outline"
              class="size-10 border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
              :aria-label="`${t('common.delete')} ${task.task_name}`"
              @click="emit('delete-task', task.id)"
            >
              <Trash2 class="h-4 w-4" />
            </Button>
          </div>
        </article>
      </template>
    </div>

    <div class="hidden lg:block">
      <Table>
        <TableHeader class="border-b border-[#c8e3f3] bg-[#eaf7ff]">
          <TableRow>
            <TableHead class="w-[80px] px-6 text-[#365773] font-bold uppercase text-[10px] tracking-wider text-center">{{ t('tasks.table.headers.status') }}</TableHead>
            <TableHead class="min-w-[300px] text-[#365773] font-bold uppercase text-[10px] tracking-wider text-left">{{ t('tasks.table.headers.details') }}</TableHead>
            <TableHead class="w-[180px] text-[#365773] font-bold uppercase text-[10px] tracking-wider text-left">{{ t('tasks.table.headers.crawl') }}</TableHead>
            <TableHead class="w-[180px] text-[#365773] font-bold uppercase text-[10px] tracking-wider text-center">{{ t('tasks.table.headers.mode') }}</TableHead>
            <TableHead class="w-[140px] text-[#365773] font-bold uppercase text-[10px] tracking-wider text-center">{{ t('tasks.table.headers.schedule') }}</TableHead>
            <TableHead class="w-[160px] px-6 text-[#365773] font-bold uppercase text-[10px] tracking-wider text-right">{{ t('tasks.table.headers.actions') }}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <template v-if="isLoading && tasks.length === 0">
            <TableRow>
              <TableCell :colspan="6" class="h-32 text-center">
                <div class="flex flex-col items-center justify-center gap-2 text-[#2b6684]">
                  <RefreshCcw class="w-6 h-6 animate-spin text-[#0e7490]" />
                  <span class="text-sm font-medium italic">{{ t('tasks.table.syncing') }}</span>
                </div>
              </TableCell>
            </TableRow>
          </template>
          <template v-else-if="tasks.length === 0">
            <TableRow>
              <TableCell :colspan="6" class="h-40 text-center">
                <div class="flex flex-col items-center justify-center gap-2 text-[#4c7d98]">
                  <Layers class="w-12 h-12 opacity-[0.45]" />
                  <p class="text-sm font-bold">{{ emptyMessage || t('tasks.table.empty') }}</p>
                </div>
              </TableCell>
            </TableRow>
          </template>
          <template v-else>
            <TableRow
              v-for="task in tasks"
              :key="task.id"
              class="group border-b border-[#d8ebf7] last:border-0 transition-colors hover:bg-[#f0fbff]"
            >
            <!-- Column 1: Status -->
            <TableCell class="px-5 align-middle">
              <div class="flex flex-col items-center gap-2">
                <Switch
                  :model-value="task.enabled"
                  class="data-[state=checked]:bg-primary scale-90"
                  @update:model-value="(val: boolean) => emit('toggle-enabled', task, val)"
                />
                <div class="flex items-center gap-1.5">
                  <div :class="[ 'w-1.5 h-1.5 rounded-full shadow-sm', task.is_running ? 'bg-emerald-500 animate-pulse' : 'bg-[#7aa4ba]' ]"></div>
                  <span :class="[ 'text-[10px] font-bold tracking-[0.12em] uppercase', task.is_running ? 'text-emerald-700' : 'text-[#52738b]' ]">
                    {{ task.is_running ? 'ACTIVE' : 'IDLE' }}
                  </span>
                </div>
              </div>
            </TableCell>

            <!-- Column 2: Task Info -->
            <TableCell class="align-middle">
              <div class="flex flex-col gap-1.5 py-1">
                <div class="flex items-center gap-2">
                  <span class="truncate text-sm font-bold tracking-tight text-slate-900 transition-colors group-hover:text-primary">{{ task.task_name }}</span>
                  <Badge 
                    variant="outline" 
                    :class="[
                      'h-5 px-1.5 text-[10px] font-semibold border-none tracking-tight',
                      isKeywordMode(task) ? 'bg-blue-50 text-blue-500' : 'bg-emerald-50 text-emerald-600'
                    ]"
                  >
                    <component :is="isKeywordMode(task) ? Keyboard : BrainCircuit" class="w-2.5 h-2.5 mr-1" />
                    {{ isKeywordMode(task) ? t('tasks.table.keywordMode') : t('tasks.table.aiMode') }}
                  </Badge>
                </div>
                
                <div class="flex items-center gap-2">
                   <div class="flex items-center gap-1.5 rounded-md border border-[#c6e2f0] bg-[#f0f9fd] px-2 py-0.5 text-[11px] font-semibold text-[#365773]">
                      <Search class="w-3 h-3 text-[#23789a]" /> {{ task.keyword }}
                   </div>
                    <div v-if="task.description" class="line-clamp-1 max-w-[220px] text-[11px] font-medium text-[#52738b]" :title="task.description">
                      {{ task.description }}
                   </div>
                </div>

                <div class="flex items-center gap-2 mt-0.5">
                    <div class="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-tight text-[#52738b]">
                      <User class="w-3 h-3" /> {{ resolveAccountStrategyLabel(task) }}
                   </div>
                   <div class="h-1 w-1 rounded-full bg-[#a8cfe1]"></div>
                    <div class="max-w-[120px] truncate text-[10px] font-medium text-[#52738b]">
                      {{ resolveAccountName(task) }}
                   </div>
                </div>
              </div>
            </TableCell>

            <!-- Column 3: Crawl Config -->
            <TableCell class="align-middle text-left">
              <div class="space-y-2">
                <div class="flex items-baseline gap-0.5">
                   <span class="mr-1 text-[10px] font-bold text-[#52738b]">¥</span>
                   <span class="text-sm font-bold tracking-tight text-[#163b57]">
                     {{ task.min_price || 0 }} <span class="mx-0.5 font-normal text-[#9cc6da]">-</span> {{ task.max_price || t('tasks.table.noUpperLimit') }}
                  </span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                   <Badge variant="outline" class="h-5 border-[#b9dced] bg-[#f0f9fd] px-1.5 text-[10px] font-semibold text-[#365773]">
                    {{ task.personal_only ? t('tasks.table.personalOnly') : t('common.all') }}
                  </Badge>
                   <Badge variant="outline" class="h-5 border-[#b9dced] bg-[#f0f9fd] px-1.5 text-[10px] font-semibold text-[#365773]">
                    {{ task.free_shipping ? t('tasks.table.freeShipping') : t('common.all') }}
                  </Badge>
                   <div v-if="task.region" class="flex h-5 max-w-[100px] items-center gap-0.5 truncate rounded border border-[#b9dced] bg-[#f0f9fd] px-1.5 text-[10px] font-semibold text-[#365773]">
                    <MapPin class="w-2.5 h-2.5" /> {{ task.region }}
                  </div>
                </div>
              </div>
            </TableCell>

            <!-- Column 4: AI/Keyword Mode Details -->
            <TableCell class="align-middle text-center">
              <div class="inline-flex flex-col items-center gap-2">
                  <div v-if="isKeywordMode(task)" class="rounded-md border border-blue-100 bg-blue-50/60 p-2">
                    <div class="text-xs font-semibold text-blue-700">{{ t('tasks.table.keywordStrategies', { count: task.keyword_rules?.length || 0 }) }}</div>
                    <div class="mt-0.5 text-[10px] font-medium text-blue-400">{{ t('tasks.table.anyKeywordMatch') }}</div>
                </div>
                <div v-else class="flex flex-col items-center gap-1.5">
                  <div 
                     class="max-w-[140px] truncate rounded-md border border-emerald-100 bg-emerald-50/60 px-2 py-1 text-[10px] font-mono font-semibold text-emerald-700"
                     :title="t('tasks.table.criteriaConfigured')"
                  >
                     {{ t('tasks.table.criteriaConfigured') }}
                  </div>
                  <Button 
                    size="sm" 
                    variant="ghost" 
                     class="h-7 px-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-700 hover:bg-emerald-50"
                    :aria-label="`${t('tasks.table.refreshCriteria')} ${task.task_name}`"
                    :title="`${t('tasks.table.refreshCriteria')} ${task.task_name}`"
                    @click="emit('refresh-criteria', task)"
                  >
                    <RefreshCcw class="w-2.5 h-2.5 mr-1" /> {{ t('tasks.table.refreshCriteria') }}
                  </Button>
                </div>
              </div>
            </TableCell>

            <!-- Column 5: Cron & Pages -->
            <TableCell class="align-middle text-center">
              <div class="inline-flex flex-col items-center gap-1.5">
                   <div class="flex items-center gap-1.5 rounded-md border border-[#b9dced] bg-[#eef8fd] px-2 py-1">
                   <Clock class="w-3 h-3 text-[#23789a]" />
                    <span class="text-[11px] font-bold tracking-tight text-[#163b57]">{{ task.cron || t('tasks.table.manualRun') }}</span>
                </div>
                <div
                  class="min-w-[112px] rounded-md border border-amber-100/80 bg-amber-50/60 px-2 py-1"
                   :class="!task.cron || !task.enabled ? 'border-[#c6e2f0] bg-[#f0f7fb]' : ''"
                  :title="resolveNextRunLabel(task) || undefined"
                >
                  <div
                     class="text-[10px] font-bold tracking-tight"
                    :class="resolveCountdownTone(task)"
                  >
                    {{ resolveCountdownText(task) }}
                  </div>
                  <div
                    v-if="resolveNextRunLabel(task)"
                     class="mt-0.5 text-[9px] font-semibold text-[#52738b]"
                  >
                    {{ resolveNextRunLabel(task) }}
                  </div>
                </div>
                 <div class="flex items-center gap-1 text-[10px] font-bold uppercase tracking-[0.12em] text-[#52738b]">
                    <Layers class="w-3 h-3" /> {{ task.max_pages || 3 }}P
                 </div>
                 <div class="flex items-center gap-1 text-[10px] font-semibold tracking-tight text-[#52738b]">
                   <span>{{ t('tasks.table.runCount', { count: historyFor(task)?.total_runs || 0 }) }}</span>
                   <span :class="(historyFor(task)?.failure_count || 0) > 0 ? 'text-rose-600' : 'text-emerald-600'">{{ t('tasks.table.failureShort', { count: historyFor(task)?.failure_count || 0 }) }}</span>
                 </div>
               </div>
            </TableCell>

            <!-- Column 6: Actions -->
            <TableCell class="px-6 align-middle text-right">
                <div class="flex justify-end items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    class="h-9 border-cyan-200 px-2.5 text-cyan-700 hover:bg-cyan-50"
                    :aria-label="`${t('tasks.console.results')} ${task.task_name}`"
                    :title="`${t('tasks.console.results')} ${task.task_name}`"
                    @click="emit('view-results', task)"
                  >
                    <Eye class="h-3.5 w-3.5" />
                    <span class="hidden xl:inline">{{ t('tasks.console.results') }}</span>
                  </Button>
                  <Button
                    v-if="!task.is_running"
                    size="sm" 
                    variant="default"
                    class="h-9 rounded-md border-none px-3 text-white shadow-sm transition-transform active:scale-[0.98]"
                    :class="task.enabled ? 'bg-primary hover:bg-primary/90' : 'bg-[#dcecf4] text-[#7a9aae] pointer-events-none opacity-80'"
                    :aria-label="`${t('tasks.table.start')} ${task.task_name}`"
                    @click="emit('run-task', task.id)"
                  >
                  <Play class="w-3 h-3 mr-1.5 fill-current" />
                  <span class="font-bold text-[11px]">{{ t('tasks.table.start') }}</span>
                </Button>
                  <Button
                    v-else
                    size="sm"
                    variant="destructive"
                    class="h-9 rounded-md border-none px-3 shadow-sm transition-transform active:scale-[0.98]"
                    :disabled="isStopping(task.id)"
                    :aria-label="`${t('tasks.table.stop')} ${task.task_name}`"
                    @click="emit('stop-task', task.id)"
                  >
                  <Square v-if="!isStopping(task.id)" class="w-3 h-3 mr-1.5 fill-current" />
                  <RefreshCcw v-else class="w-3 h-3 mr-1.5 animate-spin" />
                  <span class="font-bold text-[11px]">{{ isStopping(task.id) ? t('tasks.table.stopping') : t('tasks.table.stop') }}</span>
                </Button>

                <div class="flex items-center gap-0.5 ml-1">
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    class="h-9 w-9 rounded-md text-[#52738b] transition-colors hover:bg-[#eaf7ff] hover:text-primary"
                    :aria-label="`${t('common.edit')} ${task.task_name}`"
                    :title="`${t('common.edit')} ${task.task_name}`"
                    @click="emit('edit-task', task)"
                  >
                    <Pencil class="w-3.5 h-3.5" />
                  </Button>
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    class="h-9 w-9 rounded-md text-[#52738b] transition-colors hover:bg-rose-50 hover:text-rose-600"
                    :aria-label="`${t('common.delete')} ${task.task_name}`"
                    :title="`${t('common.delete')} ${task.task_name}`"
                    @click="emit('delete-task', task.id)"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </div>
  </div>
</template>

<style scoped>
:deep(td) {
  @apply py-3 px-4;
}
:deep(th) {
  @apply h-11 px-4;
}
</style>
