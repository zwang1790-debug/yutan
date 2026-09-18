<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useResults } from '@/composables/useResults'
import ResultsFilterBar from '@/components/results/ResultsFilterBar.vue'
import ResultsGrid from '@/components/results/ResultsGrid.vue'
import ResultsInsightsPanel from '@/components/results/ResultsInsightsPanel.vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { Database, Boxes, Sparkles } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const { t } = useI18n()

const {
  files,
  selectedFile,
  results,
  totalItems,
  insights,
  filters,
  isLoading,
  error,
  refreshResults,
  exportSelectedResults,
  deleteSelectedFile,
  toggleItemBlock,
  blacklistKeywords,
  isSavingBlacklist,
  saveBlacklistRules,
  fileOptions,
  isFileOptionsReady,
} = useResults()

const isDeleteDialogOpen = ref(false)
const isBlacklistDialogOpen = ref(false)
const blacklistDraft = ref('')

const selectedTaskLabel = computed(() => {
  if (!selectedFile.value || fileOptions.value.length === 0) return null
  const match = fileOptions.value.find((option) => option.value === selectedFile.value)
  if (!match) return null
  return match.taskName || null
})

const selectedResultLabel = computed(() => {
  if (!selectedFile.value) return t('results.filters.chooseResult')
  const match = fileOptions.value.find((option) => option.value === selectedFile.value)
  return match?.label || selectedFile.value
})

const deleteConfirmText = computed(() => {
  return selectedTaskLabel.value
    ? t('results.filters.deleteDialogWithTask', { task: selectedTaskLabel.value })
    : t('results.filters.deleteDialogFallback')
})

function openDeleteDialog() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultToDelete'),
      variant: 'destructive',
    })
    return
  }
  isDeleteDialogOpen.value = true
}

function openBlacklistDialog() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultSelected'),
      variant: 'destructive',
    })
    return
  }
  blacklistDraft.value = blacklistKeywords.value.join('\n')
  isBlacklistDialogOpen.value = true
}

function handleExportResults() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultToExport'),
      variant: 'destructive',
    })
    return
  }
  exportSelectedResults()
}

async function handleDeleteResults() {
  if (!selectedFile.value) return
  try {
    await deleteSelectedFile(selectedFile.value)
    toast({ title: t('results.filters.resultDeleted') })
  } catch (e) {
    toast({
      title: t('results.filters.deleteFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleteDialogOpen.value = false
  }
}

function parseBlacklistKeywords(input: string) {
  return input
    .split(/[\n,，]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

async function handleSaveBlacklistRules() {
  try {
    await saveBlacklistRules(parseBlacklistKeywords(blacklistDraft.value))
    toast({ title: t('results.filters.blacklistSaved') })
    isBlacklistDialogOpen.value = false
  } catch (e) {
    toast({
      title: t('results.filters.blacklistSaveFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}
</script>

<template>
  <div class="results-page page-shell relative space-y-5 overflow-hidden rounded-[28px] p-1.5 sm:p-2">
    <header class="command-hero p-5 sm:p-6">
      <div class="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div class="min-w-0">
          <div class="flex items-center gap-3">
            <span class="flex size-11 items-center justify-center rounded-2xl bg-[var(--brand-lime)] text-[var(--brand-deep)] shadow-lg shadow-black/10">
              <Database class="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p class="eyebrow text-[var(--brand-lime)]">{{ t('results.eyebrow') }}</p>
              <h1 class="mt-1 text-2xl font-black tracking-tight text-white sm:text-3xl">{{ t('results.title') }}</h1>
            </div>
          </div>
          <div class="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-white/65">
            <span class="inline-flex min-w-0 items-center gap-2 font-semibold text-white">
              <Boxes class="h-4 w-4 text-cyan-300" aria-hidden="true" />
              <span class="truncate">{{ selectedResultLabel }}</span>
            </span>
            <span class="hidden h-1 w-1 rounded-full bg-white/25 sm:block" aria-hidden="true" />
            <span class="tabular-nums">{{ t('results.resultCount', { count: totalItems }) }}</span>
          </div>
        </div>
        <div class="flex shrink-0 flex-wrap items-center gap-2">
          <span class="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-xs font-semibold text-emerald-200">
            <span class="size-1.5 animate-pulse rounded-full bg-emerald-300" aria-hidden="true" />
            {{ t('results.liveStatus') }}
          </span>
          <span class="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/[0.06] px-3 py-1.5 text-xs font-semibold text-white/60">
            <Sparkles class="h-3.5 w-3.5 text-[var(--brand-lime)]" aria-hidden="true" />
            {{ t('results.insights.panelHint') }}
          </span>
        </div>
      </div>
      <div class="pointer-events-none absolute" aria-hidden="true" />
    </header>

    <div v-if="error" class="app-alert-error mb-4" role="alert">
      <strong class="font-bold">{{ t('common.error') }}</strong>
      <span class="block sm:inline">{{ error.message }}</span>
    </div>

    <ResultsFilterBar
      :files="files"
      :file-options="fileOptions"
      :is-ready="isFileOptionsReady"
      v-model:selectedFile="selectedFile"
      v-model:aiRecommendedOnly="filters.ai_recommended_only"
      v-model:keywordRecommendedOnly="filters.keyword_recommended_only"
      v-model:includeHidden="filters.include_hidden"
      v-model:sortBy="filters.sort_by"
      v-model:sortOrder="filters.sort_order"
      :is-loading="isLoading"
      @refresh="refreshResults"
      @manage-blacklist="openBlacklistDialog"
      @export="handleExportResults"
      @delete="openDeleteDialog"
    />

    <ResultsInsightsPanel :insights="insights" :selected-task-label="selectedTaskLabel" />

    <ResultsGrid :results="results" :result-filename="selectedFile" :total-items="totalItems" :is-loading="isLoading" @toggle-block="toggleItemBlock" />

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ t('results.filters.deleteDialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ deleteConfirmText }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" :disabled="isLoading" @click="handleDeleteResults">
            {{ t('results.filters.confirmDelete') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isBlacklistDialogOpen">
      <DialogContent class="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>{{ t('results.filters.blacklistDialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ t('results.filters.blacklistDialogDescription') }}
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-2">
          <label class="text-sm font-semibold text-[#365773]">
            {{ t('results.filters.blacklistRulesLabel') }}
          </label>
          <Textarea
            v-model="blacklistDraft"
            class="min-h-[180px]"
            :placeholder="t('results.filters.blacklistRulesPlaceholder')"
          />
          <p class="text-xs leading-5 text-[#52738b]">
            {{ t('results.filters.blacklistRulesHint') }}
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isBlacklistDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button :disabled="isSavingBlacklist" @click="handleSaveBlacklistRules">
            {{ t('results.filters.confirmBlacklistSave') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
