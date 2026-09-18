<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

interface TrendPoint {
  day: string
  sample_count: number
  avg_price: number | null
  median_price: number | null
}

const props = defineProps<{
  points: TrendPoint[]
}>()
const { t } = useI18n()

const chartWidth = 720
const chartHeight = 220
const padding = 24

const validPoints = computed(() =>
  props.points.filter((point) => point.avg_price !== null && point.avg_price !== undefined)
)

const latestPoint = computed(() => validPoints.value[validPoints.value.length - 1])
const firstPoint = computed(() => validPoints.value[0])
const averageDelta = computed(() => {
  if (validPoints.value.length < 2 || !firstPoint.value || !latestPoint.value) return null
  if (firstPoint.value.avg_price === null || latestPoint.value.avg_price === null) return null
  return latestPoint.value.avg_price - firstPoint.value.avg_price
})

const trendSummary = computed(() => {
  if (validPoints.value.length === 1 && latestPoint.value) {
    return t('results.chart.singleSnapshot', {
      count: latestPoint.value.sample_count,
      price: latestPoint.value.avg_price,
    })
  }
  if (averageDelta.value === null) return t('results.chart.noTrend')
  if (Math.abs(averageDelta.value) < 0.01) return t('results.chart.stable')
  return averageDelta.value > 0
    ? t('results.chart.rising', { amount: Math.abs(averageDelta.value).toFixed(0) })
    : t('results.chart.falling', { amount: Math.abs(averageDelta.value).toFixed(0) })
})

const valueRange = computed(() => {
  const values = validPoints.value
    .flatMap((point) => [point.avg_price, point.median_price])
    .filter((value): value is number => typeof value === 'number')
  if (values.length === 0) {
    return { min: 0, max: 1 }
  }
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) {
    return { min: min - 1, max: max + 1 }
  }
  return { min, max }
})

function resolveX(index: number) {
  if (validPoints.value.length <= 1) return chartWidth / 2
  const usableWidth = chartWidth - padding * 2
  return padding + (usableWidth / (validPoints.value.length - 1)) * index
}

function resolveY(value: number) {
  const usableHeight = chartHeight - padding * 2
  const ratio = (value - valueRange.value.min) / (valueRange.value.max - valueRange.value.min)
  return chartHeight - padding - ratio * usableHeight
}

function buildPath(values: Array<number | null>) {
  const commands = values
    .map((value, index) => {
      if (value === null || value === undefined) return null
      const prefix = index === 0 ? 'M' : 'L'
      return `${prefix} ${resolveX(index)} ${resolveY(value)}`
    })
    .filter(Boolean)
  return commands.join(' ')
}

const avgPath = computed(() => buildPath(validPoints.value.map((point) => point.avg_price)))
const medianPath = computed(() => buildPath(validPoints.value.map((point) => point.median_price)))
const areaPath = computed(() => {
  if (!avgPath.value || validPoints.value.length === 0) return ''
  const firstX = resolveX(0)
  const lastX = resolveX(validPoints.value.length - 1)
  const baseline = chartHeight - padding
  return `${avgPath.value} L ${lastX} ${baseline} L ${firstX} ${baseline} Z`
})
</script>

<template>
  <div class="app-surface-subtle p-4">
    <div class="mb-3 flex flex-col gap-3 text-xs uppercase tracking-[0.22em] text-slate-500 sm:flex-row sm:items-center sm:justify-between">
      <span>{{ t('results.chart.title') }}</span>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-sky-600" />
          {{ t('results.chart.avgPrice') }}
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-amber-500" />
          {{ t('results.chart.medianPrice') }}
        </span>
      </div>
    </div>

    <div v-if="validPoints.length === 0" class="rounded-2xl border border-dashed border-slate-200 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
      {{ t('results.chart.noTrend') }}
    </div>

    <div v-else>
      <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="h-[220px] w-full" role="img" :aria-label="trendSummary">
        <defs>
          <linearGradient id="avg-area-fill" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#0284c7" stop-opacity="0.24" />
            <stop offset="100%" stop-color="#0284c7" stop-opacity="0" />
          </linearGradient>
        </defs>

        <g>
          <line
            v-for="index in 4"
            :key="index"
            :x1="padding"
            :x2="chartWidth - padding"
            :y1="padding + ((chartHeight - padding * 2) / 4) * (index - 1)"
            :y2="padding + ((chartHeight - padding * 2) / 4) * (index - 1)"
            stroke="#cbd5e1"
            stroke-dasharray="4 6"
          />
        </g>

        <path :d="areaPath" fill="url(#avg-area-fill)" />
        <path :d="avgPath" fill="none" stroke="#0284c7" stroke-width="4" stroke-linecap="round" />
        <path :d="medianPath" fill="none" stroke="#f59e0b" stroke-width="3" stroke-dasharray="8 6" stroke-linecap="round" />

        <g v-for="(point, index) in validPoints" :key="point.day">
          <circle :cx="resolveX(index)" :cy="resolveY(point.avg_price as number)" r="5" fill="#0284c7" />
          <circle v-if="point.median_price !== null && point.median_price !== undefined" :cx="resolveX(index)" :cy="resolveY(point.median_price)" r="4" fill="#f59e0b" />
          <text
            :x="resolveX(index)"
            :y="chartHeight - 6"
            text-anchor="middle"
            fill="#64748b"
            font-size="12"
          >
            {{ point.day.slice(5) }}
          </text>
        </g>
      </svg>
      <div class="mt-3 flex items-start gap-2 rounded-xl border border-sky-100 bg-sky-50/80 px-3 py-2.5 text-xs leading-5 text-sky-800" :class="validPoints.length === 1 ? 'border-amber-100 bg-amber-50/80 text-amber-800' : ''">
        <span class="mt-1 size-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" />
        <span>{{ trendSummary }}</span>
      </div>
    </div>
  </div>
</template>
