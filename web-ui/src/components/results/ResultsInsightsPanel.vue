<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ResultInsights } from '@/types/result.d.ts'
import PriceTrendChart from './PriceTrendChart.vue'
import { formatDateTime } from '@/i18n'
import { Activity, BarChart3, Clock3 } from 'lucide-vue-next'

const props = defineProps<{
  insights: ResultInsights | null
  selectedTaskLabel?: string | null
}>()
const { t } = useI18n()

const summaryCards = computed(() => {
  if (!props.insights) return []
  const market = props.insights.market_summary
  const history = props.insights.history_summary
  return [
    {
      label: t('results.insights.currentAvg'),
      value: market.avg_price ? `¥${market.avg_price}` : '—',
      hint: t('results.insights.sampleCount', { count: market.sample_count || 0 }),
    },
    {
      label: t('results.insights.historyAvg'),
      value: history.avg_price ? `¥${history.avg_price}` : '—',
      hint: t('results.insights.uniqueItems', { count: history.unique_items || 0 }),
    },
    {
      label: t('results.insights.currentMin'),
      value: market.min_price ? `¥${market.min_price}` : '—',
      hint: market.max_price
        ? t('results.insights.highestPrice', { price: market.max_price })
        : t('results.insights.noRange'),
    },
  ]
})

const businessSummary = computed(() => props.insights?.business_summary)

const businessCards = computed(() => {
  const summary = businessSummary.value
  if (!summary || summary.tracked_items === 0) return []
  return [
    {
      label: t('results.insights.trackedItems'),
      value: String(summary.tracked_items),
      hint: t('results.insights.ownedItems', { count: summary.owned_items }),
    },
    {
      label: t('results.insights.realizedProfit'),
      value: `¥${summary.realized_profit.toFixed(2)}`,
      hint: summary.realized_roi === null
        ? t('results.insights.noRoi')
        : t('results.insights.realizedRoi', { value: summary.realized_roi }),
    },
    {
      label: t('results.insights.openInventory'),
      value: `¥${summary.open_inventory_cost.toFixed(2)}`,
      hint: t('results.insights.openInventoryCount', { count: summary.open_inventory_items }),
    },
    {
      label: t('results.insights.turnoverDays'),
      value: summary.average_turnover_days === null ? '—' : `${summary.average_turnover_days}d`,
      hint: t('results.insights.turnoverSamples', { count: summary.turnover_sample_count }),
    },
  ]
})

const latestSnapshotText = computed(() => {
  if (!props.insights?.latest_snapshot_at) return t('results.insights.noSnapshot')
  return t('results.insights.latestSnapshot', {
    time: formatDateTime(props.insights.latest_snapshot_at, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }),
  })
})
</script>

<template>
  <section class="command-panel mb-6 overflow-hidden">
    <div class="border-b border-slate-200/70 bg-slate-950 px-5 py-4 text-white sm:px-6">
      <div class="flex items-center gap-2">
        <BarChart3 class="h-4 w-4 text-[var(--brand-lime)]" aria-hidden="true" />
        <p class="text-sm font-semibold text-white">{{ t('results.insights.panelTitle') }}</p>
        <span class="text-xs text-white/55">{{ t('results.insights.panelHint') }}</span>
      </div>
    </div>
    <div class="grid gap-6 px-5 py-5 lg:grid-cols-[1.15fr_0.85fr] lg:px-6">
      <div class="space-y-5">
        <div class="space-y-2">
          <p class="eyebrow text-primary/70">{{ t('results.insights.eyebrow') }}</p>
          <h2 class="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            {{ selectedTaskLabel || t('results.insights.defaultTitle') }}
          </h2>
          <p class="max-w-2xl text-sm leading-6 text-[#52738b]">
            {{ t('results.insights.subtitle') }}
          </p>
        </div>

        <div class="grid gap-4 md:grid-cols-3">
          <article
            v-for="card in summaryCards"
            :key="card.label"
            class="app-surface-subtle p-4 transition-colors hover:border-primary/20 hover:bg-primary/[0.02]"
          >
            <p class="text-xs uppercase tracking-[0.18em] text-[#52738b]">{{ card.label }}</p>
            <p class="mt-3 text-2xl font-semibold text-[#163b57]">{{ card.value }}</p>
            <p class="mt-2 text-xs text-[#52738b]">{{ card.hint }}</p>
          </article>
        </div>

        <div v-if="businessCards.length" class="space-y-3">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-bold text-[#163b57]">{{ t('results.insights.businessTitle') }}</p>
            <p v-if="businessSummary?.incomplete_sold_items" class="text-xs font-medium text-amber-700">
              {{ t('results.insights.incompleteSold', { count: businessSummary.incomplete_sold_items }) }}
            </p>
          </div>
          <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <article
              v-for="card in businessCards"
              :key="card.label"
              class="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-4"
            >
              <p class="text-xs uppercase tracking-[0.16em] text-emerald-800/70">{{ card.label }}</p>
              <p class="mt-2 text-xl font-black text-emerald-950">{{ card.value }}</p>
              <p class="mt-1 text-xs text-emerald-900/70">{{ card.hint }}</p>
            </article>
          </div>
        </div>

        <div v-if="businessSummary?.model_performance?.length" class="rounded-2xl border border-[#d8ebf7] bg-[#fbfeff] p-4">
          <div class="mb-3 flex items-center justify-between gap-3">
            <p class="text-sm font-bold text-[#163b57]">{{ t('results.insights.modelPerformance') }}</p>
            <span class="text-xs text-[#52738b]">{{ t('results.insights.modelPerformanceHint') }}</span>
          </div>
          <div class="space-y-2">
            <div
              v-for="model in businessSummary.model_performance"
              :key="model.model_key"
              class="grid grid-cols-[minmax(0,1fr)_auto_auto] items-center gap-3 rounded-xl border border-[#e5f0f6] bg-white px-3 py-2.5 text-xs"
            >
              <span class="truncate font-semibold text-[#365773]" :title="model.model_key">{{ model.model_key }}</span>
              <span class="tabular-nums text-[#52738b]">{{ model.sold_items }} {{ t('results.insights.soldUnit') }}</span>
              <span class="font-black tabular-nums" :class="model.realized_profit >= 0 ? 'text-emerald-700' : 'text-rose-700'">¥{{ model.realized_profit.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <PriceTrendChart :points="insights?.daily_trend || []" />
      </div>

      <div class="space-y-4">
        <div class="rounded-2xl border border-primary/10 bg-gradient-to-br from-primary to-sky-700 p-5 text-primary-foreground shadow-[0_16px_40px_rgba(37,99,235,0.18)]">
          <div class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-primary-foreground/70">
            <Activity class="h-4 w-4" aria-hidden="true" />
            {{ t('results.insights.trendLabel') }}
          </div>
          <p class="mt-4 text-3xl font-semibold">
            {{ t('results.insights.snapshotCount', { count: insights?.market_summary.sample_count || 0 }) }}
          </p>
          <p class="mt-2 text-sm leading-6 text-primary-foreground/80">
            {{ t('results.insights.trendReading') }}
          </p>
        </div>

          <div class="app-surface-subtle p-5">
          <div class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[#52738b]">
            <Clock3 class="h-4 w-4" aria-hidden="true" />
            {{ t('results.insights.snapshotLabel') }}
          </div>
          <p class="mt-4 text-sm leading-6 text-[#365773]">
            {{ latestSnapshotText }}
          </p>
          <div class="mt-4 grid gap-3 text-sm text-[#365773]">
            <div class="rounded-2xl border border-[#d8ebf7] bg-[#eef8fd] px-4 py-3">
              {{ t('results.insights.currentMedian') }}
                <span class="font-semibold text-[#163b57]">
                {{ insights?.market_summary.median_price ? `¥${insights.market_summary.median_price}` : '—' }}
              </span>
            </div>
            <div class="rounded-2xl border border-[#d8ebf7] bg-[#eef8fd] px-4 py-3">
              {{ t('results.insights.historyMin') }}
                <span class="font-semibold text-[#163b57]">
                {{ insights?.history_summary.min_price ? `¥${insights.history_summary.min_price}` : '—' }}
              </span>
            </div>
            <div class="rounded-2xl border border-[#d8ebf7] bg-[#eef8fd] px-4 py-3">
              {{ t('results.insights.historyMax') }}
                <span class="font-semibold text-[#163b57]">
                {{ insights?.history_summary.max_price ? `¥${insights.history_summary.max_price}` : '—' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
