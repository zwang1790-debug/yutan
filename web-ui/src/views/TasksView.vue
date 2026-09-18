<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTasks } from '@/composables/useTasks'
import { preflightTask, type TaskPreflightResponse } from '@/api/tasks'
import { getTaskHistory, type TaskHistory } from '@/api/tasks'
import type { Task, TaskUpdate } from '@/types/task.d.ts'
import { parseTaskFormDefaults } from '@/lib/taskFormQuery'
import TaskCreateDialog from '@/components/tasks/TaskCreateDialog.vue'
import TasksTable from '@/components/tasks/TasksTable.vue'
import TaskForm from '@/components/tasks/TaskForm.vue'
import { listAccounts, type AccountItem } from '@/api/accounts'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { CheckCircle2, ListTodo, XCircle, Search, RefreshCw, SlidersHorizontal, Play, Pause, Activity, Sparkles, ArrowRight } from 'lucide-vue-next'
const { t } = useI18n()

const {
  tasks,
  isLoading,
  error,
  fetchTasks,
  removeTask,
  updateTask,
  startTask,
  stopTask,
  stoppingTaskIds,
} = useTasks()
const route = useRoute()
const router = useRouter()

// State for dialogs
const isEditDialogOpen = ref(false)
const isCriteriaDialogOpen = ref(false)
const isEditSubmitting = ref(false)
const selectedTask = ref<Task | null>(null)
const criteriaTask = ref<Task | null>(null)
const criteriaDescription = ref('')
const isCriteriaSubmitting = ref(false)
const isDeleteDialogOpen = ref(false)
const taskToDeleteId = ref<number | null>(null)
const accountOptions = ref<AccountItem[]>([])
const isPreflightDialogOpen = ref(false)
const preflightResult = ref<TaskPreflightResponse | null>(null)
const preflightTaskId = ref<number | null>(null)
const isStartingAfterPreflight = ref(false)
const taskHistories = ref<Record<number, TaskHistory>>({})

const taskToDelete = computed(() => {
  if (taskToDeleteId.value === null) return null
  return tasks.value.find((task) => task.id === taskToDeleteId.value) || null
})
const editDefaults = computed(() => parseTaskFormDefaults(route.query))
const searchQuery = ref('')
const activeFilter = ref<'all' | 'running' | 'enabled' | 'paused'>('all')
const isRefreshing = ref(false)

const taskCounts = computed(() => ({
  all: tasks.value.length,
  running: tasks.value.filter((task) => task.is_running).length,
  enabled: tasks.value.filter((task) => task.enabled && !task.is_running).length,
  paused: tasks.value.filter((task) => !task.enabled).length,
}))

const activeFilterLabel = computed(() => {
  const labels = {
    all: 'tasks.console.total',
    running: 'tasks.console.running',
    enabled: 'tasks.console.enabled',
    paused: 'tasks.console.paused',
  } as const
  return t(labels[activeFilter.value])
})

const filteredTasks = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase()
  return tasks.value.filter((task) => {
    const matchesFilter = activeFilter.value === 'all'
      || (activeFilter.value === 'running' && task.is_running)
      || (activeFilter.value === 'enabled' && task.enabled && !task.is_running)
      || (activeFilter.value === 'paused' && !task.enabled)
    const haystack = [task.task_name, task.keyword, task.region, task.description].filter(Boolean).join(' ').toLocaleLowerCase()
    return matchesFilter && (!query || haystack.includes(query))
  })
})

async function refreshTaskList() {
  isRefreshing.value = true
  try {
    await fetchTasks({ silent: true })
  } finally {
    isRefreshing.value = false
  }
}

function handleDeleteTask(taskId: number) {
  taskToDeleteId.value = taskId
  isDeleteDialogOpen.value = true
}

async function handleConfirmDeleteTask() {
  if (!taskToDelete.value) {
    toast({ title: t('tasks.toasts.notFound'), variant: 'destructive' })
    isDeleteDialogOpen.value = false
    return
  }
  try {
    await removeTask(taskToDelete.value.id)
    toast({ title: t('tasks.toasts.deleted') })
  } catch (e) {
    toast({
      title: t('tasks.toasts.deleteFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleteDialogOpen.value = false
    taskToDeleteId.value = null
  }
}

function handleEditTask(task: Task) {
  selectedTask.value = task
  isEditDialogOpen.value = true
}

watch(
  () => [route.query.edit, tasks.value],
  () => {
    const editTaskId = typeof route.query.edit === 'string' ? Number(route.query.edit) : NaN
    if (!Number.isFinite(editTaskId)) return
    const match = tasks.value.find((task) => task.id === editTaskId)
    if (!match) return
    selectedTask.value = match
    isEditDialogOpen.value = true
  },
  { immediate: true }
)

async function handleUpdateTask(data: TaskUpdate) {
  if (!selectedTask.value) return
  isEditSubmitting.value = true
  try {
    await updateTask(selectedTask.value.id, data)
    isEditDialogOpen.value = false
  }
  catch (e) {
    toast({
      title: t('tasks.toasts.updateFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
  finally {
    isEditSubmitting.value = false
  }
}

function handleOpenCriteriaDialog(task: Task) {
  criteriaTask.value = task
  criteriaDescription.value = task.description || ''
  isCriteriaDialogOpen.value = true
}

async function handleRefreshCriteria() {
  if (!criteriaTask.value) return
  if (!criteriaDescription.value.trim()) {
    toast({
      title: t('tasks.toasts.descriptionRequired'),
      description: t('tasks.criteria.descriptionRequired'),
      variant: 'destructive',
    })
    return
  }

  isCriteriaSubmitting.value = true
  try {
    await updateTask(criteriaTask.value.id, { description: criteriaDescription.value })
    isCriteriaDialogOpen.value = false
  } catch (e) {
    toast({
      title: t('tasks.toasts.regenerateFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isCriteriaSubmitting.value = false
  }
}

async function handleStartTask(taskId: number) {
  preflightTaskId.value = taskId
  try {
    preflightResult.value = await preflightTask(taskId)
    if (!preflightResult.value.ready) {
      isPreflightDialogOpen.value = true
      return
    }
  } catch (e) {
    toast({ title: t('tasks.toasts.startFailed'), description: (e as Error).message, variant: 'destructive' })
    return
  }
  try {
    await startTask(taskId)
  } catch (e) {
    toast({
      title: t('tasks.toasts.startFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function confirmStartAfterPreflight() {
  if (preflightTaskId.value === null) return
  isStartingAfterPreflight.value = true
  try {
    await startTask(preflightTaskId.value)
    isPreflightDialogOpen.value = false
  } catch (e) {
    toast({ title: t('tasks.toasts.startFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isStartingAfterPreflight.value = false
  }
}

function repairPreflight(checkKey: string) {
  const task = tasks.value.find((item) => item.id === preflightTaskId.value)
  if (checkKey === 'ai') {
    isPreflightDialogOpen.value = false
    router.push({ path: '/settings', query: { tab: 'ai' } })
    return
  }
  if (checkKey === 'account') {
    isPreflightDialogOpen.value = false
    router.push('/accounts')
    return
  }
  if (checkKey === 'criteria' && task) {
    criteriaTask.value = task
    criteriaDescription.value = task.description || ''
    isPreflightDialogOpen.value = false
    isCriteriaDialogOpen.value = true
  }
}

function handleViewResults(task: Task) {
  router.push({ path: '/results', query: { keyword: task.keyword } })
}

function clearTaskFilters() {
  searchQuery.value = ''
  activeFilter.value = 'all'
}

function openCreateTask() {
  router.push({ path: '/tasks', query: { create: '1' } })
}

function openSettings() {
  router.push('/settings')
}

async function handleStopTask(taskId: number) {
  try {
    await stopTask(taskId)
  } catch (e) {
    toast({
      title: t('tasks.toasts.stopFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function handleToggleEnabled(task: Task, enabled: boolean) {
  const previous = task.enabled
  task.enabled = enabled
  try {
    await updateTask(task.id, { enabled })
  } catch (e) {
    task.enabled = previous
    toast({
      title: t('tasks.toasts.toggleFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function fetchAccountOptions() {
  try {
    accountOptions.value = await listAccounts()
  } catch (e) {
    toast({
      title: t('tasks.toasts.loadAccountsFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function fetchTaskHistories() {
  const entries = await Promise.all(
    tasks.value.map(async (task) => [task.id, await getTaskHistory(task.id)] as const)
  )
  taskHistories.value = Object.fromEntries(entries)
}

onMounted(fetchAccountOptions)
onMounted(async () => {
  await fetchTasks()
  await fetchTaskHistories()
})
</script>

<template>
  <div class="task-page relative space-y-5 overflow-hidden rounded-[28px] p-1.5 sm:p-2 animate-fade-in">
    <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <p class="eyebrow mb-2">{{ t('tasks.console.eyebrow') }}</p>
        <h1 class="page-heading flex items-center gap-3">
          <span class="flex size-10 items-center justify-center rounded-2xl bg-[var(--brand-deep)] text-[var(--brand-lime)] shadow-lg shadow-slate-950/10">
            <ListTodo class="h-5 w-5" />
          </span>
          {{ t('tasks.title') }}
        </h1>
        <p class="mt-2 max-w-2xl text-sm font-semibold text-[#365773]">{{ t('tasks.console.description') }}</p>
      </div>
      <TaskCreateDialog :account-options="accountOptions" @created="fetchTasks" />
    </div>

    <section class="task-status-rail overflow-hidden" aria-label="Task status filters">
      <div class="grid gap-2 sm:grid-cols-4">
        <button
          v-for="item in [
            { key: 'all', label: t('tasks.console.total'), value: taskCounts.all, icon: ListTodo, tone: 'text-white' },
            { key: 'running', label: t('tasks.console.running'), value: taskCounts.running, icon: Activity, tone: 'text-[var(--brand-lime)]' },
            { key: 'enabled', label: t('tasks.console.enabled'), value: taskCounts.enabled, icon: Play, tone: 'text-cyan-300' },
            { key: 'paused', label: t('tasks.console.paused'), value: taskCounts.paused, icon: Pause, tone: 'text-amber-300' },
          ]"
          :key="item.key"
          type="button"
          class="task-status-tile group"
          :class="activeFilter === item.key ? 'task-status-tile-active' : ''"
          :aria-pressed="activeFilter === item.key"
          @click="activeFilter = item.key as 'all' | 'running' | 'enabled' | 'paused'"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="text-[11px] font-bold uppercase tracking-[0.14em] text-white/75">{{ item.label }}</span>
            <component :is="item.icon" class="h-4 w-4" :class="item.tone" aria-hidden="true" />
          </div>
          <div class="mt-2 flex items-end justify-between gap-2">
            <span class="text-2xl font-black tabular-nums text-white">{{ item.value }}</span>
            <span v-if="item.key === 'running' && item.value" class="mb-1 inline-flex items-center gap-1 text-[10px] font-semibold text-[var(--brand-lime)]">
              <span class="size-1.5 animate-pulse rounded-full bg-[var(--brand-lime)]" /> LIVE
            </span>
          </div>
        </button>
      </div>
    </section>

    <!-- Edit Task Dialog -->
    <Dialog v-model:open="isEditDialogOpen">
      <DialogContent class="sm:max-w-[640px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ t('tasks.editDialog.title', { task: selectedTask?.task_name || "" }) }}</DialogTitle>
        </DialogHeader>
        <TaskForm
          v-if="selectedTask"
          mode="edit"
          :initial-data="selectedTask"
          :account-options="accountOptions"
          :default-values="editDefaults"
          @submit="(data) => handleUpdateTask(data as TaskUpdate)"
        />
        <DialogFooter>
          <Button type="submit" form="task-form" :disabled="isEditSubmitting">
            {{ isEditSubmitting ? t('common.saving') : t('tasks.editDialog.save') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Refresh Criteria Dialog -->
    <Dialog v-model:open="isCriteriaDialogOpen">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{{ t('tasks.criteria.title') }}</DialogTitle>
          <DialogDescription>
            {{ t('tasks.criteria.description') }}
          </DialogDescription>
        </DialogHeader>
        <div class="grid gap-3">
          <label class="text-sm font-medium text-slate-700">{{ t('tasks.form.description') }}</label>
          <Textarea
            v-model="criteriaDescription"
            class="min-h-[140px]"
            :placeholder="t('tasks.form.descriptionPlaceholder')"
          />
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isCriteriaDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button :disabled="isCriteriaSubmitting" @click="handleRefreshCriteria">
            {{ isCriteriaSubmitting ? t('tasks.criteria.generating') : t('tasks.criteria.action') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <div v-if="error" class="app-alert-error mb-4" role="alert">
      <strong class="font-bold">{{ t('common.error') }}</strong>
      <span class="block sm:inline">{{ error.message }}</span>
    </div>

    <section v-if="tasks.length" class="command-panel overflow-hidden border-[#c8e3f3] shadow-[0_18px_45px_-32px_rgba(14,116,144,0.8)]">
      <div class="flex flex-col gap-3 border-b border-[#d8ebf7] bg-white p-3 sm:flex-row sm:items-center sm:justify-between sm:p-4">
        <div class="relative min-w-0 flex-1 sm:max-w-xl">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#23789a]" aria-hidden="true" />
          <Input v-model="searchQuery" class="h-10 border-[#b9dced] bg-[#f3faff] pl-9 pr-3 text-[#163b57] placeholder:text-[#6c879d] focus-visible:ring-[#14b8d4]" :placeholder="t('tasks.console.searchPlaceholder')" />
        </div>
        <div class="flex items-center justify-between gap-3 sm:justify-end">
          <span class="text-xs font-bold tabular-nums text-[#365773]">{{ t('tasks.console.showing', { visible: filteredTasks.length, total: tasks.length }) }}</span>
          <Button variant="outline" size="sm" :disabled="isRefreshing" :aria-label="t('tasks.console.refresh')" @click="refreshTaskList">
            <RefreshCw class="h-3.5 w-3.5" :class="isRefreshing ? 'animate-spin' : ''" />
            <span class="hidden sm:inline">{{ t('tasks.console.refresh') }}</span>
          </Button>
        </div>
      </div>
      <div class="flex items-center justify-between gap-3 border-b border-[#d8ebf7] bg-[#eaf7ff] px-3 py-2.5 sm:px-4">
        <div class="flex min-w-0 items-center gap-2 text-xs text-[#365773]">
          <SlidersHorizontal class="h-3.5 w-3.5 text-primary" aria-hidden="true" />
          <span class="font-bold text-[#1d4f70]">{{ activeFilterLabel }}</span>
           <span class="hidden truncate font-medium text-[#52738b] sm:inline">· {{ t('tasks.console.description') }}</span>
        </div>
        <button v-if="searchQuery || activeFilter !== 'all'" type="button" class="shrink-0 text-xs font-bold text-primary hover:underline" @click="clearTaskFilters">
          {{ t('tasks.console.clearFilters') }}
        </button>
      </div>
    </section>

    <section v-if="!tasks.length && !isLoading" class="command-panel-dark relative overflow-hidden p-6 sm:p-8">
      <div class="pointer-events-none absolute -right-10 -top-16 size-56 rounded-full bg-cyan-400/15 blur-3xl" />
      <div class="relative grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          <div class="mb-4 inline-flex size-12 items-center justify-center rounded-2xl bg-[var(--brand-lime)] text-[var(--brand-deep)] shadow-xl shadow-black/10">
            <Sparkles class="h-6 w-6" aria-hidden="true" />
          </div>
          <p class="eyebrow text-[var(--brand-lime)]">{{ t('tasks.console.emptyTitle') }}</p>
          <h2 class="mt-3 max-w-xl text-2xl font-black tracking-tight text-white sm:text-3xl">{{ t('tasks.console.emptyDescription') }}</h2>
          <div class="mt-6 flex flex-wrap gap-2">
            <Button class="bg-[var(--brand-lime)] text-[var(--brand-deep)] hover:bg-lime-300" @click="openCreateTask">
              {{ t('tasks.console.emptyAction') }}
              <ArrowRight class="h-4 w-4" aria-hidden="true" />
            </Button>
            <Button variant="outline" class="border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white" @click="openSettings">
              {{ t('tasks.console.emptySettings') }}
            </Button>
          </div>
        </div>
        <div class="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
          <div v-for="(step, index) in [t('tasks.console.emptyStepOne'), t('tasks.console.emptyStepTwo'), t('tasks.console.emptyStepThree')]" :key="step" class="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.06] px-4 py-3">
            <span class="flex size-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-sm font-black text-[var(--brand-lime)]">0{{ index + 1 }}</span>
            <span class="text-sm font-semibold text-white/80">{{ step }}</span>
          </div>
        </div>
      </div>
    </section>

    <TasksTable
      v-else
      :tasks="filteredTasks"
      :is-loading="isLoading"
      :stopping-ids="stoppingTaskIds"
      :histories="taskHistories"
      :empty-message="t('tasks.console.noMatch')"
      @delete-task="handleDeleteTask"
      @edit-task="handleEditTask"
      @run-task="handleStartTask"
      @stop-task="handleStopTask"
      @refresh-criteria="handleOpenCriteriaDialog"
      @toggle-enabled="handleToggleEnabled"
      @view-results="handleViewResults"
    />

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ t('tasks.deleteDialog.title') }}</DialogTitle>
          <DialogDescription>
            {{ taskToDelete ? t('tasks.deleteDialog.descriptionWithTask', { task: taskToDelete.task_name }) : t('tasks.deleteDialog.descriptionFallback') }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" @click="handleConfirmDeleteTask">{{ t('tasks.deleteDialog.confirm') }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isPreflightDialogOpen">
      <DialogContent class="sm:max-w-[620px]">
        <DialogHeader>
          <DialogTitle>任务启动前检查</DialogTitle>
          <DialogDescription>{{ preflightResult?.task_name }}：{{ preflightResult?.summary }}</DialogDescription>
        </DialogHeader>
        <div class="space-y-3">
          <div v-for="check in preflightResult?.checks" :key="check.key" class="rounded-lg border p-3" :class="check.passed ? 'border-emerald-200 bg-emerald-50/60' : 'border-red-200 bg-red-50/70'">
            <div class="flex items-start gap-3">
              <CheckCircle2 v-if="check.passed" class="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
              <XCircle v-else class="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
              <div>
                <p class="font-semibold">{{ check.label }}</p>
                <p class="mt-1 text-sm text-[#365773]">{{ check.detail }}</p>
                <p v-if="check.fix" class="mt-1 text-sm font-medium text-amber-700">修复建议：{{ check.fix }}</p>
                <Button
                  v-if="!check.passed && ['ai', 'account', 'criteria'].includes(check.key)"
                  variant="link"
                  size="sm"
                  class="mt-1 h-auto px-0 text-primary"
                  @click="repairPreflight(check.key)"
                >
                  {{ check.key === 'criteria' ? '重新生成分析标准' : check.key === 'account' ? '前往账号管理' : '前往 AI 设置' }}
                </Button>
              </div>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isPreflightDialogOpen = false">取消</Button>
          <Button v-if="preflightResult?.ready" :disabled="isStartingAfterPreflight" @click="confirmStartAfterPreflight">{{ isStartingAfterPreflight ? '启动中...' : '确认启动' }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
