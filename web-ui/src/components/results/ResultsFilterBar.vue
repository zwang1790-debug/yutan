<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Archive, Download, Eye, Filter, RefreshCw, ShieldBan, SlidersHorizontal, Trash2 } from 'lucide-vue-next'

interface FileOption {
  value: string
  label: string
  taskName?: string
}

interface Props {
  files: string[]
  fileOptions?: FileOption[]
  selectedFile: string | null
  aiRecommendedOnly: boolean
  keywordRecommendedOnly: boolean
  includeHidden: boolean
  sortBy: 'crawl_time' | 'publish_time' | 'price' | 'keyword_hit_count' | 'opportunity_score'
  sortOrder: 'asc' | 'desc'
  isLoading: boolean
  isReady: boolean
}

const props = defineProps<Props>()
const { t } = useI18n()

const options = computed(() => {
  if (!props.isReady) return []
  if (props.fileOptions && props.fileOptions.length > 0) return props.fileOptions
  return props.files.map((file) => ({ value: file, label: file }))
})

const selectedLabel = computed(() => {
  if (!props.isReady) return t('results.filters.loadingTaskNames')
  if (options.value.length === 0) return t('results.filters.noResults')
  if (!props.selectedFile) return t('results.filters.chooseResult')
  const match = options.value.find((option) => option.value === props.selectedFile)
  return match ? match.label : t('results.filters.taskNameLabel', { task: t('common.unnamed') })
})

const labelClass = computed(() => {
  const classes = ['transition-opacity', 'duration-200']
  if (!props.isReady || !props.selectedFile || options.value.length === 0) classes.push('text-muted-foreground')
  classes.push(props.isReady ? 'opacity-100' : 'opacity-70')
  return classes.join(' ')
})

const isSelectDisabled = computed(() => !props.isReady || options.value.length === 0)

const emit = defineEmits<{
  (e: 'update:selectedFile', value: string): void
  (e: 'update:aiRecommendedOnly', value: boolean): void
  (e: 'update:keywordRecommendedOnly', value: boolean): void
  (e: 'update:includeHidden', value: boolean): void
  (e: 'update:sortBy', value: 'crawl_time' | 'publish_time' | 'price' | 'keyword_hit_count' | 'opportunity_score'): void
  (e: 'update:sortOrder', value: 'asc' | 'desc'): void
  (e: 'refresh'): void
  (e: 'export'): void
  (e: 'delete'): void
  (e: 'manage-blacklist'): void
}>()

function handleToggleAiRecommended(value: boolean) {
  emit('update:aiRecommendedOnly', value)
  if (value) emit('update:keywordRecommendedOnly', false)
}

function handleToggleKeywordRecommended(value: boolean) {
  emit('update:keywordRecommendedOnly', value)
  if (value) emit('update:aiRecommendedOnly', false)
}
</script>

<template>
  <section class="command-panel mb-6 overflow-hidden">
    <div class="border-b border-slate-200/70 bg-slate-950 px-4 py-3 text-white sm:px-5">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex items-start gap-3">
          <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[var(--brand-lime)] text-[var(--brand-deep)]">
            <Archive class="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <p class="text-sm font-semibold text-white">{{ t('results.filters.sourceTitle') }}</p>
            <p class="mt-0.5 text-xs text-white/55">{{ t('results.filters.sourceHint') }}</p>
          </div>
        </div>
        <div class="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" class="min-h-10" @click="emit('refresh')" :disabled="props.isLoading">
            <RefreshCw class="mr-1.5 h-4 w-4" :class="{ 'animate-spin': props.isLoading }" aria-hidden="true" />
            {{ t('common.refresh') }}
          </Button>
          <Button variant="outline" size="sm" class="min-h-10" @click="emit('manage-blacklist')" :disabled="props.isLoading || !props.selectedFile">
            <ShieldBan class="mr-1.5 h-4 w-4" aria-hidden="true" />
            {{ t('results.filters.manageBlacklist') }}
          </Button>
          <Button variant="outline" size="sm" class="min-h-10" @click="emit('export')" :disabled="props.isLoading || !props.selectedFile">
            <Download class="mr-1.5 h-4 w-4" aria-hidden="true" />
            {{ t('results.filters.exportCsv') }}
          </Button>
          <Button variant="destructive" size="sm" class="min-h-10" @click="emit('delete')" :disabled="props.isLoading || !props.selectedFile">
            <Trash2 class="mr-1.5 h-4 w-4" aria-hidden="true" />
            {{ t('results.filters.deleteResult') }}
          </Button>
        </div>
      </div>
    </div>

    <div class="space-y-5 p-4 sm:p-5">
      <div class="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)]">
        <div class="space-y-2">
          <Label class="text-xs font-bold text-[#365773]">{{ t('results.filters.resultFileLabel') }}</Label>
          <Select :model-value="props.selectedFile || undefined" @update:model-value="(value) => emit('update:selectedFile', value as string)">
            <SelectTrigger class="w-full" :disabled="isSelectDisabled">
              <span :class="labelClass">{{ selectedLabel }}</span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="option in options" :key="option.value" :value="option.value">
                {{ option.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <Label class="text-xs font-bold text-[#365773]">{{ t('results.filters.sortLabel') }}</Label>
          <Select :model-value="props.sortBy" @update:model-value="(value) => emit('update:sortBy', value as any)">
            <SelectTrigger class="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="crawl_time">{{ t('results.filters.sortByCrawlTime') }}</SelectItem>
              <SelectItem value="publish_time">{{ t('results.filters.sortByPublishTime') }}</SelectItem>
              <SelectItem value="price">{{ t('results.filters.sortByPrice') }}</SelectItem>
              <SelectItem value="keyword_hit_count">{{ t('results.filters.sortByKeywordHits') }}</SelectItem>
              <SelectItem value="opportunity_score">{{ t('results.filters.sortByOpportunity') }}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div class="space-y-2">
          <Label class="text-xs font-bold text-[#365773]">{{ t('results.filters.orderLabel') }}</Label>
          <Select :model-value="props.sortOrder" @update:model-value="(value) => emit('update:sortOrder', value as any)">
            <SelectTrigger class="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="desc">{{ t('results.filters.desc') }}</SelectItem>
              <SelectItem value="asc">{{ t('results.filters.asc') }}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div class="rounded-xl border border-[#d8ebf7] bg-[#fbfeff] p-3 sm:p-4">
        <div class="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.16em] text-[#365773]">
          <SlidersHorizontal class="h-4 w-4 text-primary" aria-hidden="true" />
          {{ t('results.filters.filterTitle') }}
        </div>
        <div class="grid gap-3 sm:grid-cols-3">
          <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-[#c8e3f3] bg-[#eef8fd] px-3 text-sm font-medium text-[#365773] transition-colors hover:border-primary/50 hover:bg-[#e2f5fc]">
            <Checkbox id="ai-recommended-only" :model-value="props.aiRecommendedOnly" @update:modelValue="(value) => handleToggleAiRecommended(value === true)" />
            <span class="flex items-center gap-2"><Filter class="h-4 w-4 text-emerald-600" aria-hidden="true" />{{ t('results.filters.aiOnly') }}</span>
          </label>
          <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-[#c8e3f3] bg-[#eef8fd] px-3 text-sm font-medium text-[#365773] transition-colors hover:border-primary/50 hover:bg-[#e2f5fc]">
            <Checkbox id="keyword-recommended-only" :model-value="props.keywordRecommendedOnly" @update:modelValue="(value) => handleToggleKeywordRecommended(value === true)" />
            <span class="flex items-center gap-2"><Filter class="h-4 w-4 text-amber-600" aria-hidden="true" />{{ t('results.filters.keywordOnly') }}</span>
          </label>
          <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-[#c8e3f3] bg-[#eef8fd] px-3 text-sm font-medium text-[#365773] transition-colors hover:border-primary/50 hover:bg-[#e2f5fc]">
            <Checkbox id="include-hidden" :model-value="props.includeHidden" @update:modelValue="(value) => emit('update:includeHidden', value === true)" />
            <span class="flex items-center gap-2"><Eye class="h-4 w-4 text-slate-500" aria-hidden="true" />{{ t('results.filters.includeHidden') }}</span>
          </label>
        </div>
      </div>
    </div>
  </section>
</template>
