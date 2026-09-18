<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDashboard } from '@/composables/useDashboard'
import { Button } from '@/components/ui/button'
import Badge from '@/components/ui/badge/Badge.vue'
import PriceTrendChart from '@/components/results/PriceTrendChart.vue'
import { formatNumber, formatRelativeTimeFromNow } from '@/i18n'
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Eye,
  Gauge,
  ListPlus,
  Play,
  Radio,
  RefreshCw,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  Workflow,
} from 'lucide-vue-next'

const router = useRouter()
const { t } = useI18n()
const {
  snapshot,
  focusInsights,
  focusTask,
  suggestion,
  stats,
  taskSummaries,
  activities,
  isLoading,
  error,
  fetchSummary,
} = useDashboard()

const headlineStats = computed(() => [
  {
    label: t('dashboard.command.liveTasks'),
    value: String(stats.value.runningTasks),
    detail: t('dashboard.command.ofEnabled', { count: stats.value.enabledTasks }),
    icon: Radio,
    tone: 'text-cyan-200',
  },
  {
    label: t('dashboard.command.scannedItems'),
    value: formatNumber(stats.value.scannedItems),
    detail: t('dashboard.command.resultFiles', { count: stats.value.resultFiles }),
    icon: Search,
    tone: 'text-emerald-200',
  },
  {
    label: t('dashboard.command.recommendations'),
    value: formatNumber(stats.value.recommendedItems),
    detail: t('dashboard.command.recommendationBreakdown', {
      ai: stats.value.aiRecommendedItems,
      keyword: stats.value.keywordRecommendedItems,
    }),
    icon: Target,
    tone: 'text-amber-200',
  },
])

const listedTasks = computed(() => taskSummaries.value.slice(0, 5))
const runningTasks = computed(() => taskSummaries.value.filter((task) => task.is_running))
const attentionItems = computed(() => {
  if (taskSummaries.value.length === 0) {
    return [{
      key: 'first-task',
      title: t('dashboard.attention.firstTaskTitle'),
      description: t('dashboard.attention.firstTaskDescription'),
      action: t('dashboard.attention.firstTaskAction'),
      route: 'create',
      icon: ListPlus,
      tone: 'amber',
    }]
  }

  const waitingForResults = taskSummaries.value.filter((task) => task.enabled && !task.filename)
  const pausedTasks = taskSummaries.value.filter((task) => !task.enabled)
  const items = waitingForResults.slice(0, 2).map((task) => ({
    key: `results-${task.task_id}`,
    title: t('dashboard.attention.waitingResultsTitle', { task: task.task_name }),
    description: t('dashboard.attention.waitingResultsDescription'),
    action: t('dashboard.attention.openTask'),
    route: task.task_id ? 'task' : 'tasks',
    taskId: task.task_id,
    icon: Clock3,
    tone: 'amber',
  }))

  if (items.length < 3) {
    items.push(...pausedTasks.slice(0, 3 - items.length).map((task) => ({
      key: `paused-${task.task_id}`,
      title: t('dashboard.attention.pausedTitle', { task: task.task_name }),
      description: t('dashboard.attention.pausedDescription'),
      action: t('dashboard.attention.openTask'),
      route: task.task_id ? 'task' : 'tasks',
      taskId: task.task_id,
      icon: CircleAlert,
      tone: 'slate',
    })))
  }

  return items
})

const hasAllClear = computed(() => taskSummaries.value.length > 0 && attentionItems.value.length === 0)

const focusTitle = computed(() => focusTask.value?.task_name || t('dashboard.focus.defaultTitle'))
const focusMeta = computed(() => {
  if (!focusTask.value) return t('dashboard.focus.empty')
  const keyword = focusTask.value.keyword || t('dashboard.focus.missingKeyword')
  const count = focusTask.value.total_items
  return t('dashboard.focus.meta', { keyword, count })
})

const insightCards = computed(() => {
  const market = focusInsights.value?.market_summary
  const history = focusInsights.value?.history_summary
  return [
    {
      label: t('results.insights.currentAvg'),
      value: market?.avg_price ? `¥${market.avg_price}` : '—',
      hint: market
        ? t('results.insights.sampleCount', { count: market.sample_count })
        : t('results.grid.empty'),
    },
    {
      label: t('results.insights.historyAvg'),
      value: history?.avg_price ? `¥${history.avg_price}` : '—',
      hint: history
        ? t('results.insights.uniqueItems', { count: history.unique_items })
        : t('results.insights.noSnapshot'),
    },
    {
      label: t('results.insights.currentMin'),
      value: market?.min_price !== null && market?.min_price !== undefined ? `¥${market.min_price}` : '—',
      hint: market?.max_price
        ? t('results.insights.highestPrice', { price: market.max_price })
        : t('results.insights.noRange'),
    },
  ]
})

function goCreateTask() {
  router.push({
    name: 'Tasks',
    query: { create: '1' },
  })
}

function openTask(taskId: number | null | undefined) {
  router.push({
    name: 'Tasks',
    query: taskId ? { edit: String(taskId) } : undefined,
  })
}

function openResults(filename: string | null) {
  if (!filename) {
    goCreateTask()
    return
  }
  router.push({ name: 'Results', query: { file: filename } })
}

function handleAttentionAction(item: { route: string; taskId?: number | null }) {
  if (item.route === 'create') {
    goCreateTask()
    return
  }
  openTask(item.taskId)
}

function openSuggestion() {
  router.push({
    name: suggestion.value.routeName,
    query: suggestion.value.query,
  })
}

function openActivity(activity: { filename: string | null; type: string }) {
  if (activity.filename) {
    router.push({ name: 'Results', query: { file: activity.filename } })
    return
  }
  if (activity.type === 'task') {
    router.push({ name: 'Tasks' })
    return
  }
  router.push({ name: 'Dashboard' })
}
</script>

<template>
  <div class="dashboard-page relative space-y-5 overflow-hidden rounded-[28px] p-1.5 sm:p-2 animate-fade-in">
    <div v-if="error" class="app-alert-error" role="alert">
      {{ error.message }}
    </div>
    <section class="command-hero p-5 sm:p-7 lg:p-8">
      <div class="relative z-10 flex flex-col gap-6">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div class="max-w-2xl">
            <div class="flex flex-wrap items-center gap-2">
              <span class="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-cyan-100">
                <span class="relative flex size-2">
                  <span v-if="stats.runningTasks" class="dashboard-breathe absolute inline-flex size-2 rounded-full bg-cyan-300" />
                  <span class="relative inline-flex size-2 rounded-full" :class="stats.runningTasks ? 'bg-cyan-300' : 'bg-slate-500'" />
                </span>
                {{ stats.runningTasks ? t('dashboard.command.liveSignal') : t('dashboard.command.standbySignal') }}
              </span>
              <span class="text-xs text-cyan-100/75">
                {{ t('dashboard.command.lastSync', { time: formatRelativeTimeFromNow(snapshot?.summary.last_updated_at) }) }}
              </span>
            </div>
            <p class="mt-5 text-xs font-bold uppercase tracking-[0.22em] text-cyan-100/75">{{ t('dashboard.command.eyebrow') }}</p>
            <h1 class="mt-2 text-3xl font-bold tracking-[-0.04em] text-white sm:text-4xl">
              {{ taskSummaries.length ? t('dashboard.command.title') : t('dashboard.command.emptyTitle') }}
            </h1>
            <p class="mt-3 max-w-xl text-sm leading-6 text-sky-100/90 sm:text-base">
              {{ taskSummaries.length ? t('dashboard.command.description') : t('dashboard.command.emptyDescription') }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button variant="outline" class="border-slate-600 bg-slate-900/55 text-slate-100 hover:border-cyan-300/50 hover:bg-slate-800 hover:text-white" :aria-label="t('dashboard.command.refresh')" @click="fetchSummary">
              <RefreshCw :class="['h-4 w-4', isLoading && 'animate-spin']" />
              {{ t('dashboard.command.refresh') }}
            </Button>
            <Button class="bg-cyan-300 text-slate-950 shadow-lg shadow-cyan-400/10 hover:bg-cyan-200" @click="goCreateTask">
              <ListPlus class="h-4 w-4" />
              {{ t('dashboard.createTask') }}
            </Button>
          </div>
        </div>

        <template v-if="taskSummaries.length">
          <div class="grid gap-3 sm:grid-cols-3">
            <article v-for="stat in headlineStats" :key="stat.label" class="command-panel-dark border-cyan-300/20 bg-[#0a1f36]/80 p-4">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-cyan-100/75">{{ stat.label }}</p>
                  <p class="mt-2 text-3xl font-bold tabular-nums tracking-[-0.04em] text-white">{{ stat.value }}</p>
                </div>
                <component :is="stat.icon" :class="['h-5 w-5', stat.tone]" />
              </div>
              <p class="mt-3 text-xs text-sky-100/70">{{ stat.detail }}</p>
            </article>
          </div>
          <div class="grid gap-3 lg:grid-cols-[1.25fr_0.75fr]">
            <div class="rounded-xl border border-cyan-300/15 bg-slate-950/30 p-4">
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2">
                  <Workflow class="h-4 w-4 text-cyan-200" />
                  <span class="text-sm font-semibold text-white">{{ t('dashboard.command.activeFlow') }}</span>
                </div>
                <span class="text-xs text-cyan-100/75">{{ t('dashboard.command.runningCount', { count: runningTasks.length }) }}</span>
              </div>
              <div class="mt-4 space-y-3">
                <div v-for="task in runningTasks.slice(0, 2)" :key="task.task_id || task.task_name" class="rounded-lg border border-cyan-300/15 bg-cyan-300/5 px-3 py-2.5">
                  <div class="flex items-center justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate text-sm font-semibold text-white">{{ task.task_name }}</p>
                      <p class="mt-0.5 truncate text-xs text-cyan-100/65">{{ task.keyword }}</p>
                    </div>
                    <span class="inline-flex shrink-0 items-center gap-1.5 text-xs font-semibold text-cyan-100"><span class="dashboard-breathe size-1.5 rounded-full bg-cyan-300" />{{ t('dashboard.command.collecting') }}</span>
                  </div>
                  <div class="relative mt-2 h-1.5 overflow-hidden rounded-full bg-cyan-950/70">
                    <span class="dashboard-sweep absolute inset-y-0 w-1/3 rounded-full bg-gradient-to-r from-transparent via-cyan-200 to-transparent" />
                  </div>
                </div>
                <p v-if="runningTasks.length === 0" class="text-sm text-sky-100/75">{{ t('dashboard.command.noLiveTask') }}</p>
              </div>
            </div>
            <div class="rounded-xl border border-emerald-300/15 bg-emerald-300/5 p-4">
              <div class="flex items-center gap-2"><Gauge class="h-4 w-4 text-emerald-200" /><span class="text-sm font-semibold text-white">{{ t('dashboard.command.resultPulse') }}</span></div>
              <p class="mt-4 text-2xl font-bold tabular-nums text-white">{{ formatNumber(stats.recommendedItems) }}</p>
              <p class="mt-1 text-xs leading-5 text-emerald-100/65">{{ t('dashboard.command.resultPulseDescription') }}</p>
            </div>
          </div>
        </template>

        <div v-else class="grid gap-3 lg:grid-cols-[1.1fr_0.9fr]">
          <div class="rounded-xl border border-dashed border-cyan-300/35 bg-slate-950/30 p-5 sm:p-6">
            <div class="flex size-11 items-center justify-center rounded-xl bg-cyan-300 text-slate-950"><Play class="ml-0.5 h-5 w-5 fill-current" /></div>
            <h2 class="mt-5 text-lg font-bold text-white">{{ t('dashboard.onboarding.title') }}</h2>
            <p class="mt-2 max-w-lg text-sm leading-6 text-slate-300">{{ t('dashboard.onboarding.description') }}</p>
            <Button class="mt-5 bg-cyan-300 text-slate-950 hover:bg-cyan-200" @click="goCreateTask"><ListPlus class="h-4 w-4" />{{ t('dashboard.onboarding.action') }}</Button>
          </div>
          <ol class="grid gap-2 sm:grid-cols-3 lg:grid-cols-1">
            <li v-for="step in ['task', 'run', 'result']" :key="step" class="rounded-xl border border-cyan-300/20 bg-[#0a1f36]/80 p-4">
              <span class="text-xs font-bold text-cyan-200">0{{ step === 'task' ? 1 : step === 'run' ? 2 : 3 }}</span>
              <p class="mt-2 text-sm font-semibold text-white">{{ t(`dashboard.onboarding.${step}Title`) }}</p>
              <p class="mt-1 text-xs leading-5 text-sky-100/75">{{ t(`dashboard.onboarding.${step}Description`) }}</p>
            </li>
          </ol>
        </div>
      </div>
    </section>

    <div v-if="taskSummaries.length" class="grid items-start gap-5 xl:grid-cols-[1.25fr_0.75fr]">
      <section class="command-panel overflow-hidden">
        <div class="flex flex-col gap-3 border-b border-[#d8ebf7] bg-white p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="eyebrow">{{ t('dashboard.queue.eyebrow') }}</p>
            <h2 class="mt-1 text-lg font-bold tracking-[-0.02em] text-slate-950">{{ t('dashboard.queue.title') }}</h2>
          </div>
          <Button variant="ghost" size="sm" class="w-fit text-primary" @click="router.push({ name: 'Tasks' })">{{ t('dashboard.queue.viewAll') }}<ArrowRight class="h-3.5 w-3.5" /></Button>
        </div>
        <div class="divide-y divide-slate-100">
          <article v-for="task in listedTasks" :key="task.task_id || task.task_name" class="group grid gap-3 border-b border-[#e1f0f7] p-4 transition-colors hover:bg-[#f0fbff] sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center sm:px-5">
            <button class="min-w-0 text-left" @click="openTask(task.task_id)">
              <div class="flex flex-wrap items-center gap-2">
                <span class="size-2 rounded-full" :class="task.is_running ? 'dashboard-breathe bg-emerald-500' : task.enabled ? 'bg-cyan-500' : 'bg-[#7aa4ba]'" />
                <span class="truncate text-sm font-bold text-[#163b57] group-hover:text-primary">{{ task.task_name }}</span>
                <Badge variant="outline" :class="task.is_running ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : task.enabled ? 'border-cyan-200 bg-cyan-50 text-cyan-700' : 'border-[#b9dced] bg-[#eef8fd] text-[#52738b]'">{{ task.is_running ? t('dashboard.queue.running') : task.enabled ? t('dashboard.queue.ready') : t('dashboard.queue.paused') }}</Badge>
              </div>
              <p class="mt-1 truncate text-xs text-[#52738b]">{{ task.keyword }}<span v-if="task.region"> · {{ task.region }}</span><span v-if="task.latest_crawl_time"> · {{ t('dashboard.queue.updated', { time: formatRelativeTimeFromNow(task.latest_crawl_time) }) }}</span></p>
            </button>
            <div class="flex items-center gap-4 text-xs sm:justify-end">
              <div><p class="text-[#52738b]">{{ t('dashboard.queue.samples') }}</p><p class="mt-1 font-bold tabular-nums text-[#163b57]">{{ formatNumber(task.total_items) }}</p></div>
              <div><p class="text-[#52738b]">{{ t('dashboard.queue.hits') }}</p><p class="mt-1 font-bold tabular-nums text-emerald-700">{{ formatNumber(task.recommended_items) }}</p></div>
            </div>
            <Button size="sm" variant="outline" class="w-full sm:w-auto" :disabled="!task.filename" @click="openResults(task.filename)"><Eye class="h-3.5 w-3.5" />{{ t('dashboard.queue.preview') }}</Button>
          </article>
        </div>
      </section>

      <aside class="space-y-5">
        <section class="command-panel p-5">
          <div class="flex items-start justify-between gap-3"><div><p class="eyebrow">{{ t('dashboard.trend.eyebrow') }}</p><h2 class="mt-1 text-lg font-bold text-slate-950">{{ focusTitle }}</h2><p class="mt-1 text-xs text-slate-500">{{ focusMeta }}</p></div><TrendingUp class="h-5 w-5 shrink-0 text-primary" /></div>
          <div v-if="focusTask?.filename" class="mt-4 space-y-3">
            <div class="grid grid-cols-3 gap-2"><div v-for="card in insightCards" :key="card.label" class="rounded-lg border border-[#d8ebf7] bg-[#eef8fd] p-2.5"><p class="text-[10px] leading-4 text-[#52738b]">{{ card.label }}</p><p class="mt-1 truncate text-sm font-bold tabular-nums text-[#163b57]">{{ card.value }}</p></div></div>
            <PriceTrendChart :points="focusInsights?.daily_trend || []" />
            <Button variant="outline" class="w-full" @click="openResults(focusTask.filename)"><TrendingUp class="h-4 w-4" />{{ t('dashboard.trend.openResults') }}</Button>
          </div>
          <div v-else class="mt-4 rounded-xl border border-dashed border-[#b9dced] bg-[#eef8fd] p-4 text-center"><Search class="mx-auto h-5 w-5 text-[#7aa4ba]" /><p class="mt-2 text-sm font-semibold text-[#365773]">{{ t('dashboard.trend.emptyTitle') }}</p><p class="mt-1 text-xs leading-5 text-[#52738b]">{{ t('dashboard.trend.emptyDescription') }}</p></div>
        </section>

        <section class="command-panel p-5">
          <div class="flex items-center justify-between"><div class="flex items-center gap-2"><CircleAlert class="h-4 w-4 text-amber-500" /><h2 class="text-sm font-bold text-slate-950">{{ t('dashboard.attention.title') }}</h2></div><span v-if="hasAllClear" class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700"><CheckCircle2 class="h-3.5 w-3.5" />{{ t('dashboard.attention.allClear') }}</span></div>
          <div v-if="attentionItems.length" class="mt-3 space-y-2"><article v-for="item in attentionItems" :key="item.key" class="rounded-lg border p-3" :class="item.tone === 'amber' ? 'border-amber-200 bg-amber-50/80' : 'border-[#c8e3f3] bg-[#eef8fd]'"><div class="flex gap-2.5"><component :is="item.icon" class="mt-0.5 h-4 w-4 shrink-0" :class="item.tone === 'amber' ? 'text-amber-600' : 'text-[#52738b]'" /><div class="min-w-0"><p class="text-xs font-semibold text-[#163b57]">{{ item.title }}</p><p class="mt-1 text-xs leading-5 text-[#52738b]">{{ item.description }}</p><button type="button" class="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline" @click="handleAttentionAction(item)">{{ item.action }}<ArrowRight class="h-3 w-3" /></button></div></div></article></div>
          <p v-else class="mt-3 text-sm text-[#52738b]">{{ t('dashboard.attention.empty') }}</p>
        </section>
      </aside>
    </div>

    <div v-if="taskSummaries.length" class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <section class="command-panel overflow-hidden">
        <div class="flex items-center justify-between border-b border-[#d8ebf7] bg-white p-5"><div class="flex items-center gap-2"><Sparkles class="h-4 w-4 text-primary" /><h2 class="text-sm font-bold text-[#163b57]">{{ t('dashboard.discoveries.title') }}</h2></div><Button variant="ghost" size="sm" class="text-primary" @click="router.push({ name: 'Results' })">{{ t('dashboard.discoveries.viewAll') }}<ArrowRight class="h-3.5 w-3.5" /></Button></div>
        <div v-if="taskSummaries.some((task) => task.latest_recommended_title)" class="divide-y divide-[#e1f0f7]"><button v-for="task in taskSummaries.filter((item) => item.latest_recommended_title).slice(0, 3)" :key="`discovery-${task.task_id}`" class="flex w-full items-center gap-3 p-4 text-left transition-colors hover:bg-[#f0fbff]" @click="openResults(task.filename)"><div class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600"><Target class="h-4 w-4" /></div><div class="min-w-0 flex-1"><p class="truncate text-sm font-semibold text-[#163b57]">{{ task.latest_recommended_title }}</p><p class="mt-0.5 truncate text-xs text-[#52738b]">{{ task.task_name }} · {{ task.keyword }}</p></div><p class="shrink-0 text-sm font-bold tabular-nums text-emerald-700">{{ task.latest_recommended_price ? `¥${task.latest_recommended_price}` : '—' }}</p></button></div>
        <div v-else class="p-6 text-center"><Target class="mx-auto h-6 w-6 text-slate-200" /><p class="mt-2 text-sm font-semibold text-slate-700">{{ t('dashboard.discoveries.emptyTitle') }}</p><p class="mt-1 text-xs leading-5 text-slate-500">{{ t('dashboard.discoveries.emptyDescription') }}</p></div>
      </section>

      <section class="command-panel overflow-hidden">
        <div class="flex items-center justify-between border-b border-[#d8ebf7] bg-white p-5"><div class="flex items-center gap-2"><Activity class="h-4 w-4 text-rose-500" /><h2 class="text-sm font-bold text-[#163b57]">{{ t('dashboard.activity.title') }}</h2></div><Button variant="ghost" size="sm" class="text-primary" @click="router.push({ name: 'Logs' })">{{ t('dashboard.activity.viewAllLogs') }}<ArrowRight class="h-3.5 w-3.5" /></Button></div>
        <div v-if="activities.length" class="divide-y divide-[#e1f0f7]"><button v-for="activity in activities.slice(0, 5)" :key="activity.id" class="flex w-full items-center gap-3 p-3.5 text-left transition-colors hover:bg-[#f0fbff]" @click="openActivity(activity)"><span class="size-2 shrink-0 rounded-full" :class="activity.type === 'recommendation' ? 'bg-emerald-500' : activity.type === 'task' ? 'bg-cyan-500' : 'bg-amber-500'" /><div class="min-w-0 flex-1"><p class="truncate text-sm font-semibold text-[#163b57]">{{ activity.title }}</p><p class="mt-0.5 truncate text-xs text-[#52738b]">{{ activity.task_name }}<span v-if="activity.detail"> · {{ activity.detail }}</span></p></div><span class="shrink-0 text-[11px] text-[#52738b]">{{ formatRelativeTimeFromNow(activity.timestamp) }}</span></button></div>
        <p v-else class="p-5 text-sm text-[#52738b]">{{ t('dashboard.activity.empty') }}</p>
      </section>
    </div>

    <section v-if="taskSummaries.length" class="rounded-xl border border-primary/15 bg-primary/[0.035] p-5 sm:flex sm:items-center sm:justify-between">
      <div><p class="eyebrow text-primary/70">{{ t('dashboard.suggestion.sectionTitle') }}</p><p class="mt-1 font-semibold text-slate-900">{{ suggestion.title }}</p><p class="mt-1 max-w-3xl text-sm text-slate-600">{{ suggestion.description }}</p></div>
      <Button class="mt-4 shrink-0 sm:mt-0" @click="openSuggestion"><Sparkles class="h-4 w-4" />{{ suggestion.actionLabel }}</Button>
    </section>
  </div>
</template>
