<script setup lang="ts">
import type { ResultItem } from '@/types/result.d.ts'
import { useI18n } from 'vue-i18n'
import ResultCard from './ResultCard.vue'
import { Inbox, SearchX } from 'lucide-vue-next'

interface Props {
  results: ResultItem[]
  resultFilename: string | null
  totalItems?: number
  isLoading: boolean
}

const props = defineProps<Props>()
const { t } = useI18n()

const emit = defineEmits<{
  (e: 'toggle-block', item: ResultItem): void
}>()
const skeletonItems = Array.from({ length: 8 }, (_, index) => index)
</script>

<template>
  <div :aria-busy="isLoading">
    <div
      v-if="isLoading"
      class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      aria-live="polite"
    >
      <div
        v-for="item in skeletonItems"
        :key="item"
        class="app-surface overflow-hidden"
      >
        <div class="aspect-[4/3] animate-pulse bg-slate-200/70"></div>
        <div class="space-y-3 p-4">
          <div class="h-5 w-4/5 animate-pulse rounded bg-slate-200/70"></div>
          <div class="h-7 w-1/3 animate-pulse rounded bg-slate-200/70"></div>
          <div class="rounded-xl border border-slate-100 bg-slate-50/80 p-3">
            <div class="h-4 w-1/2 animate-pulse rounded bg-slate-200/70"></div>
            <div class="mt-3 h-2 w-full animate-pulse rounded bg-slate-200/70"></div>
            <div class="mt-3 h-4 w-full animate-pulse rounded bg-slate-200/70"></div>
            <div class="mt-2 h-4 w-3/4 animate-pulse rounded bg-slate-200/70"></div>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="props.results.length === 0" class="app-surface px-6 py-16 text-center">
      <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-[#c8e3f3] bg-[#eaf7ff] text-[#52738b]">
        <SearchX class="h-6 w-6" aria-hidden="true" />
      </div>
      <h2 class="mt-4 text-base font-semibold text-slate-900">{{ t('results.grid.emptyTitle') }}</h2>
      <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-[#52738b]">{{ t('results.grid.empty') }}</p>
      <div class="mt-4 inline-flex items-center gap-2 text-xs text-[#52738b]">
        <Inbox class="h-4 w-4" aria-hidden="true" />
        {{ t('results.grid.emptyHint') }}
      </div>
    </div>
    <div v-else>
      <div class="mb-3 flex items-center justify-between gap-3 px-1">
        <p class="text-sm font-bold text-[#163b57]">{{ t('results.grid.sectionTitle') }}</p>
        <p class="text-xs font-medium text-[#52738b]">{{ t('results.grid.visibleCount', { count: props.results.length, total: props.totalItems ?? props.results.length }) }}</p>
      </div>
      <div class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <ResultCard v-for="item in props.results" :key="item.商品信息.商品ID" :item="item" :filename="props.resultFilename" @toggle-block="emit('toggle-block', $event)" />
      </div>
    </div>
  </div>
</template>
