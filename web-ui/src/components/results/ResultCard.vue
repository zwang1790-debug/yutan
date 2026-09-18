<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { InventoryStatus, ResultItem } from '@/types/result.d.ts'
import { saveInventoryRecord, saveProfitEstimate as saveProfitEstimateApi } from '@/api/results'
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import Badge from '@/components/ui/badge/Badge.vue'
import { ExternalLink, TrendingUp, TrendingDown, Info, User, Clock, MapPin, CheckCircle2, XCircle, AlertCircle, EyeOff, Eye, Save, ClipboardList, Crosshair } from 'lucide-vue-next'
import { formatDateTime } from '@/i18n'

interface Props {
  item: ResultItem
  filename: string | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'toggle-block', item: ResultItem): void
}>()
const { t } = useI18n()

const info = props.item.商品信息
const seller = props.item.卖家信息
const ai = props.item.ai_analysis
const priceInsight = props.item.price_insight
const opportunity = props.item.opportunity_assessment
const pricing = props.item.pricing_assessment

const isRecommended = ai?.is_recommended === true
const recommendationStatus = computed(() => {
  if (ai?.is_recommended === true) return { label: t('results.card.strongRecommend'), color: 'bg-emerald-500', icon: CheckCircle2, text: 'text-emerald-600', bg: 'bg-emerald-50' }
  if (ai?.is_recommended === false) return { label: t('results.card.notRecommended'), color: 'bg-rose-500', icon: XCircle, text: 'text-rose-600', bg: 'bg-rose-50' }
  return { label: t('results.card.pending'), color: 'bg-amber-500', icon: AlertCircle, text: 'text-amber-600', bg: 'bg-amber-50' }
})

const imageUrl = info.商品图片列表?.[0] || info.商品主图链接 || ''
const crawlTime = props.item.爬取时间
  ? formatDateTime(props.item.爬取时间, { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  : t('common.unknown')
const matchScore = ai?.value_score ?? 0
const isHidden = computed(() => props.item._effective_hidden === true || props.item._status === 'hidden')
const isRuleHidden = computed(() => props.item._hidden_reason === 'rule')
const canToggleBlock = computed(() => props.item._hidden_reason !== 'rule' && props.item._hidden_reason !== 'expired')
const hiddenLabel = computed(() => {
  if (props.item._hidden_reason === 'rule') return t('results.card.blacklisted')
  if (props.item._hidden_reason === 'expired') return t('results.card.expired')
  return t('results.card.hidden')
})

const expanded = ref(false)

function parsePrice(value?: string | number | null) {
  if (value === undefined || value === null) return null
  const text = String(value).replace(/[¥￥,\s]/g, '').trim()
  if (!text || ['价格异常', '暂无', '-', 'N/A'].includes(text)) return null
  const number = Number(text.replace(/万$/, ''))
  if (!Number.isFinite(number)) return null
  return text.endsWith('万') ? number * 10000 : number
}

const savedEstimate = props.item.profit_estimate
const initialPurchasePrice = savedEstimate?.purchase_price ?? parsePrice(info.当前售价) ?? 0
const suggestedResalePrice = priceInsight?.market_p50_price
  ?? priceInsight?.market_median_price
  ?? priceInsight?.market_avg_price
  ?? parsePrice(info.当前售价)
  ?? 0
const costPrice = ref(initialPurchasePrice)
const sellingPrice = ref(savedEstimate?.resale_price ?? suggestedResalePrice)
const platformFee = ref(savedEstimate?.platform_fee ?? 0)
const shippingCost = ref(savedEstimate?.shipping_cost ?? 0)
const otherCost = ref(savedEstimate?.other_cost ?? 0)
const isSavingEstimate = ref(false)
const estimateSaved = ref(Boolean(savedEstimate))
const estimateError = ref(false)

const inventory = props.item.inventory_record
const inventoryStatus = ref<InventoryStatus>(inventory?.status ?? 'discovered')
const actualPurchasePrice = ref<number | null>(inventory?.actual_purchase_price ?? null)
const actualSalePrice = ref<number | null>(inventory?.actual_sale_price ?? null)
const actualPlatformFee = ref(inventory?.actual_platform_fee ?? 0)
const actualShippingCost = ref(inventory?.actual_shipping_cost ?? 0)
const actualOtherCost = ref(inventory?.actual_other_cost ?? 0)
const inventoryNotes = ref(inventory?.notes ?? '')
const isSavingInventory = ref(false)
const inventorySaved = ref(Boolean(inventory))
const inventoryError = ref(false)

const actualProfit = computed(() => {
  if (actualPurchasePrice.value === null || actualSalePrice.value === null) return null
  return actualSalePrice.value - actualPurchasePrice.value - actualPlatformFee.value - actualShippingCost.value - actualOtherCost.value
})
const actualMargin = computed(() => {
  if (actualProfit.value === null || !actualSalePrice.value) return null
  return (actualProfit.value / actualSalePrice.value) * 100
})

const profit = computed(() => {
  const purchase = costPrice.value || 0
  const revenue = sellingPrice.value || 0
  return revenue - purchase - platformFee.value - shippingCost.value - otherCost.value
})
const margin = computed(() => {
  const revenue = sellingPrice.value || 0
  return revenue > 0 ? (profit.value / revenue) * 100 : 0
})

async function handleSaveProfitEstimate() {
  if (!props.filename || !info.商品ID) return
  isSavingEstimate.value = true
  estimateError.value = false
  try {
    await saveProfitEstimateApi(props.filename, info.商品ID, {
      purchase_price: costPrice.value || 0,
      resale_price: sellingPrice.value || 0,
      platform_fee: platformFee.value || 0,
      shipping_cost: shippingCost.value || 0,
      other_cost: otherCost.value || 0,
    })
    estimateSaved.value = true
  } catch {
    estimateError.value = true
  } finally {
    isSavingEstimate.value = false
  }
}

async function handleSaveInventory() {
  if (!props.filename || !info.商品ID) return
  isSavingInventory.value = true
  inventoryError.value = false
  try {
    await saveInventoryRecord(props.filename, info.商品ID, {
      status: inventoryStatus.value,
      actual_purchase_price: actualPurchasePrice.value,
      actual_sale_price: actualSalePrice.value,
      actual_platform_fee: actualPlatformFee.value || 0,
      actual_shipping_cost: actualShippingCost.value || 0,
      actual_other_cost: actualOtherCost.value || 0,
      notes: inventoryNotes.value,
    })
    inventorySaved.value = true
  } catch {
    inventoryError.value = true
  } finally {
    isSavingInventory.value = false
  }
}
</script>

<template>
  <Card class="group flex h-full flex-col overflow-hidden rounded-2xl border-[#c8e3f3] bg-white shadow-[0_10px_26px_rgba(14,116,144,0.08)] transition-[transform,box-shadow,opacity] duration-200 hover:-translate-y-0.5 hover:shadow-[0_18px_34px_rgba(14,116,144,0.16)]" :class="{ 'opacity-55': isHidden }">
    <!-- Image Header -->
    <div class="relative aspect-[4/3] overflow-hidden">
      <div class="absolute inset-0 animate-pulse bg-[#eaf7ff]" v-if="!imageUrl"></div>
      <img
        v-else
        :src="imageUrl"
        :alt="info.商品标题"
         class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        loading="lazy"
      />
      <!-- Hidden overlay -->
      <div v-if="isHidden" class="absolute inset-0 bg-black/30 flex items-center justify-center">
        <span class="rounded-full border border-white/20 bg-slate-950/60 px-3 py-1.5 text-xs font-semibold tracking-wide text-white backdrop-blur-sm">{{ hiddenLabel }}</span>
      </div>
      <!-- Overlays -->
      <div class="absolute top-3 left-3 flex gap-2">
        <Badge v-if="isRecommended && !isHidden" variant="default" class="bg-emerald-500/90 backdrop-blur-md border-none shadow-sm">
          {{ t('results.card.curated') }}
        </Badge>
        <Badge v-if="isRuleHidden" variant="secondary" class="bg-slate-900/75 text-white border-none backdrop-blur-md shadow-sm">
          {{ t('results.card.blacklisted') }}
        </Badge>
      </div>
      <div class="absolute top-3 right-3 flex gap-1.5">
        <button
          v-if="canToggleBlock"
          type="button"
          @click="emit('toggle-block', props.item)"
          :aria-label="isHidden ? t('results.card.unblock') : t('results.card.block')"
           class="flex min-h-10 min-w-10 items-center justify-center rounded-full border border-white/40 bg-white/30 p-2.5 text-white opacity-100 shadow-sm backdrop-blur-md transition-[background-color,opacity] hover:bg-white/55 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white sm:opacity-0 sm:group-hover:opacity-100"
        >
          <EyeOff v-if="!isHidden" class="w-4 h-4" />
          <Eye v-else class="w-4 h-4" />
        </button>
         <a
           :href="info.商品链接"
           target="_blank"
           rel="noopener noreferrer"
           :aria-label="t('results.card.detail')"
            class="flex min-h-10 min-w-10 items-center justify-center rounded-full border border-white/40 bg-white/30 p-2.5 text-white opacity-100 shadow-sm backdrop-blur-md transition-[background-color,opacity] hover:bg-white/55 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white sm:opacity-0 sm:group-hover:opacity-100"
         >
            <ExternalLink class="w-4 h-4" />
         </a>
      </div>
    </div>

    <CardHeader class="p-4 pb-3">
      <div class="flex justify-between items-start gap-3">
        <CardTitle class="min-h-11 flex-grow text-base font-semibold leading-snug text-slate-900 line-clamp-2">
          <a :href="info.商品链接" target="_blank" rel="noopener noreferrer" class="transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
            {{ info.商品标题 }}
          </a>
        </CardTitle>
      </div>
      <div class="mt-3 flex items-baseline gap-2">
        <span class="text-2xl font-bold tracking-tight text-rose-600 tabular-nums">{{ info.当前售价 }}</span>
        <span v-if="info['商品原价']" class="mb-1 text-xs text-[#7a9aae] line-through">{{ info['商品原价'] }}</span>
      </div>
      <div class="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-[#52738b]">
        <span v-if="info.发货地区" class="inline-flex items-center gap-1"><MapPin class="h-3.5 w-3.5" aria-hidden="true" />{{ info.发货地区 }}</span>
        <span v-if="ai?.keyword_hit_count" class="inline-flex items-center gap-1"><span class="h-1.5 w-1.5 rounded-full bg-amber-500" aria-hidden="true" />{{ t('results.card.keywordHits', { count: ai.keyword_hit_count }) }}</span>
      </div>
    </CardHeader>

    <CardContent class="p-4 pt-2 flex-grow">
      <!-- AI Insight Section -->
      <div class="rounded-xl border border-slate-200/70 p-3.5" :class="recommendationStatus.bg">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <component :is="recommendationStatus.icon" class="w-4 h-4" :class="recommendationStatus.text" />
            <span class="text-sm font-bold" :class="recommendationStatus.text">{{ recommendationStatus.label }}</span>
          </div>
          <div class="flex items-center gap-1">
             <span class="text-[10px] font-medium uppercase tracking-wider text-[#52738b]">{{ t('results.card.aiMatch') }}</span>
             <span class="text-sm font-black" :class="recommendationStatus.text">{{ matchScore }}%</span>
          </div>
        </div>
        
        <div class="w-full h-1.5 bg-white/50 rounded-full overflow-hidden mb-3">
           <div
             class="h-full rounded-full transition-[width] duration-300 ease-out"
            :class="recommendationStatus.color"
            :style="{ width: `${matchScore}%` }"
          ></div>
        </div>

        <p class="text-xs leading-relaxed text-[#365773]" :class="{ 'line-clamp-2': !expanded }">
           {{ ai?.reason || t('results.card.analyzing') }}
        </p>
        
        <button
          type="button"
          v-if="ai?.reason && ai.reason.length > 50"
          @click="expanded = !expanded" 
          class="mt-2 inline-flex min-h-8 items-center gap-1 text-xs font-semibold text-primary/80 transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
        >
          {{ expanded ? t('results.card.collapse') : t('results.card.expand') }}
          <Info class="w-3 h-3" />
        </button>
      </div>

      <!-- Price Stats Grid -->
      <div v-if="priceInsight?.observation_count || priceInsight?.market_sample_count" class="mt-4 grid grid-cols-2 gap-3">
        <div class="rounded-xl border border-[#d8ebf7] bg-[#eef8fd] p-3">
          <div class="mb-1 flex items-center gap-1.5 text-[10px] font-medium text-[#52738b]">
            <TrendingUp class="w-3 h-3" /> {{ t('results.card.marketAvg') }}
          </div>
          <div class="text-sm font-bold text-slate-700">
            {{ priceInsight.market_p50_price ?? priceInsight.market_avg_price ? `¥${priceInsight.market_p50_price ?? priceInsight.market_avg_price}` : '—' }}
          </div>
        </div>
        <div class="rounded-xl border border-[#d8ebf7] bg-[#eef8fd] p-3">
          <div class="mb-1 flex items-center gap-1.5 text-[10px] font-medium text-[#52738b]">
            <TrendingDown class="w-3 h-3" /> {{ t('results.card.historicalLow') }}
          </div>
          <div class="text-sm font-bold text-slate-700">
            {{ priceInsight.min_price ? `¥${priceInsight.min_price}` : '—' }}
          </div>
        </div>
      </div>

      <section v-if="opportunity && !pricing" class="mt-4 rounded-xl border border-violet-200/80 bg-violet-50/70 p-3">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-2 text-violet-900">
            <Crosshair class="h-4 w-4" aria-hidden="true" />
            <span class="text-xs font-black uppercase tracking-wider">{{ t('results.card.opportunityTitle') }}</span>
          </div>
          <span class="rounded-full px-2 py-0.5 text-xs font-black" :class="opportunity.score === null ? 'bg-slate-200 text-slate-600' : opportunity.score >= 75 ? 'bg-emerald-200 text-emerald-800' : opportunity.score >= 55 ? 'bg-amber-200 text-amber-800' : 'bg-rose-100 text-rose-700'">
            {{ opportunity.score === null ? t('results.card.dataInsufficient') : `${opportunity.score} ${t('results.card.opportunityScore')}` }}
          </span>
        </div>
        <p class="mt-2 text-sm font-bold text-violet-950">{{ opportunity.label }}</p>
        <div v-if="opportunity.score !== null" class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div class="rounded-lg border border-violet-100 bg-white/80 p-2">
            <p class="text-violet-700/70">{{ t('results.card.maxPurchasePrice') }}</p>
            <p class="mt-1 font-black text-violet-950">¥{{ opportunity.recommended_max_purchase_price?.toFixed(0) ?? '—' }}</p>
          </div>
          <div class="rounded-lg border border-violet-100 bg-white/80 p-2">
            <p class="text-violet-700/70">{{ t('results.card.suggestedListingPrice') }}</p>
            <p class="mt-1 font-black text-violet-950">¥{{ opportunity.suggested_listing_price?.toFixed(0) ?? '—' }}</p>
          </div>
          <div class="rounded-lg border border-violet-100 bg-white/80 p-2">
            <p class="text-violet-700/70">{{ t('results.card.expectedProfit') }}</p>
            <p class="mt-1 font-black" :class="(opportunity.expected_profit ?? 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'">¥{{ opportunity.expected_profit?.toFixed(0) ?? '—' }}</p>
          </div>
          <div class="rounded-lg border border-violet-100 bg-white/80 p-2">
            <p class="text-violet-700/70">{{ t('results.card.referenceSamples') }}</p>
            <p class="mt-1 font-black text-violet-950">{{ opportunity.market_sample_count }} {{ t('results.card.samplesUnit') }}</p>
          </div>
        </div>
        <p v-if="opportunity.reasons[0]" class="mt-3 text-xs leading-5 text-violet-900/75">{{ opportunity.reasons[0] }}</p>
        <p v-if="opportunity.risk_notes.length" class="mt-1 text-xs font-medium text-rose-700">{{ t('results.card.riskSignals') }}{{ opportunity.risk_notes.join('、') }}</p>
      </section>

      <section v-if="pricing" class="mt-4 rounded-xl border border-cyan-200/80 bg-cyan-50/70 p-3">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="flex items-center gap-2 text-cyan-950">
              <Crosshair class="h-4 w-4" aria-hidden="true" />
              <span class="text-xs font-black uppercase tracking-wider">市场定价</span>
            </div>
            <p class="mt-1 text-sm font-bold text-cyan-950">{{ pricing.label }}</p>
          </div>
          <span class="rounded-full bg-white px-2 py-0.5 text-[11px] font-bold text-cyan-800">
            {{ pricing.market_sample_count }}/{{ pricing.market_raw_sample_count }} 有效样本
          </span>
        </div>
        <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div class="rounded-lg border border-cyan-100 bg-white/80 p-2">
            <p class="text-cyan-700/70">P25 保守价</p>
            <p class="mt-1 font-black text-cyan-950">¥{{ pricing.price_band.p25 !== null ? Math.round(pricing.price_band.p25) : '—' }}</p>
          </div>
          <div class="rounded-lg border border-cyan-100 bg-white/80 p-2">
            <p class="text-cyan-700/70">P50 市场价</p>
            <p class="mt-1 font-black text-cyan-950">¥{{ pricing.price_band.p50 !== null ? Math.round(pricing.price_band.p50) : '—' }}</p>
          </div>
          <div class="rounded-lg border border-cyan-100 bg-white/80 p-2">
            <p class="text-cyan-700/70">快速出货价</p>
            <p class="mt-1 font-black text-cyan-950">¥{{ pricing.quick_sale_price !== null ? Math.round(pricing.quick_sale_price) : '—' }}</p>
          </div>
          <div class="rounded-lg border border-cyan-100 bg-white/80 p-2">
            <p class="text-cyan-700/70">最高收货价</p>
            <p class="mt-1 font-black text-cyan-950">¥{{ pricing.recommended_max_purchase_price !== null ? Math.round(pricing.recommended_max_purchase_price) : '—' }}</p>
          </div>
        </div>
        <p v-if="pricing.reasons[0]" class="mt-3 text-xs leading-5 text-cyan-900/75">{{ pricing.reasons[0] }}</p>
        <p v-if="pricing.reasons[1]" class="mt-1 text-xs leading-5 text-cyan-900/75">{{ pricing.reasons[1] }}</p>
        <p v-if="pricing.risk_notes.length" class="mt-1 text-xs font-medium text-rose-700">风险信号：{{ pricing.risk_notes.join('、') }}</p>
      </section>

      <details class="mt-4 rounded-xl border border-amber-200/70 bg-amber-50/60 p-3">
        <summary class="cursor-pointer list-none text-xs font-semibold uppercase tracking-wider text-amber-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500/40">{{ t('results.card.profitEstimator') }}</summary>
        <p v-if="priceInsight?.market_median_price || priceInsight?.market_avg_price" class="mt-2 text-xs leading-5 text-amber-800/75">
          {{ t('results.card.marketResaleHint', { price: priceInsight?.market_median_price || priceInsight?.market_avg_price }) }}
        </p>
        <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <label class="text-[#365773]">{{ t('results.card.purchasePrice') }}
            <input v-model.number="costPrice" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-amber-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/40" />
          </label>
          <label class="text-[#365773]">{{ t('results.card.resalePrice') }}
            <input v-model.number="sellingPrice" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-amber-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/40" />
          </label>
          <label class="text-[#365773]">{{ t('results.card.platformFee') }}
            <input v-model.number="platformFee" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-amber-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/40" />
          </label>
          <label class="text-[#365773]">{{ t('results.card.shippingCost') }}
            <input v-model.number="shippingCost" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-amber-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/40" />
          </label>
          <label class="col-span-2 text-[#365773]">{{ t('results.card.otherCost') }}
            <input v-model.number="otherCost" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-amber-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400/40" />
          </label>
        </div>
        <div class="mt-3 flex items-end justify-between border-t border-amber-200/70 pt-3">
          <div>
            <p class="text-[10px] uppercase tracking-wider text-amber-700">{{ t('results.card.estimatedProfit') }}</p>
            <p class="text-xl font-black" :class="profit >= 0 ? 'text-emerald-700' : 'text-rose-700'">¥{{ profit.toFixed(2) }}</p>
          </div>
          <p class="text-xs text-[#52738b]">{{ t('results.card.margin') }} {{ margin.toFixed(1) }}%</p>
        </div>
        <button
          type="button"
          class="mt-3 inline-flex min-h-9 w-full items-center justify-center gap-2 rounded-md bg-amber-700 px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-amber-800 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isSavingEstimate || !props.filename || !info.商品ID"
          @click="handleSaveProfitEstimate"
        >
          <Save class="h-3.5 w-3.5" aria-hidden="true" />
          {{ isSavingEstimate ? t('results.card.savingEstimate') : estimateSaved ? t('results.card.updateEstimate') : t('results.card.saveEstimate') }}
        </button>
        <p v-if="estimateError" class="mt-2 text-xs font-medium text-rose-700" role="alert">
          {{ t('results.card.saveEstimateFailed') }}
        </p>
      </details>

      <details class="mt-4 rounded-xl border border-cyan-200/70 bg-cyan-50/60 p-3">
        <summary class="flex cursor-pointer list-none items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cyan-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/40">
          <ClipboardList class="h-3.5 w-3.5" aria-hidden="true" />
          {{ t('results.card.inventoryTracker') }}
        </summary>
        <div class="mt-3 space-y-3 text-xs">
          <label class="block text-[#365773]">{{ t('results.card.inventoryStatus') }}
            <select v-model="inventoryStatus" class="mt-1 min-h-10 w-full rounded-md border border-cyan-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/40">
              <option value="discovered">{{ t('results.card.statusDiscovered') }}</option>
              <option value="contacting">{{ t('results.card.statusContacting') }}</option>
              <option value="purchased">{{ t('results.card.statusPurchased') }}</option>
              <option value="listed">{{ t('results.card.statusListed') }}</option>
              <option value="sold">{{ t('results.card.statusSold') }}</option>
              <option value="skipped">{{ t('results.card.statusSkipped') }}</option>
            </select>
          </label>
          <div class="grid grid-cols-2 gap-2">
            <label class="text-[#365773]">{{ t('results.card.actualPurchasePrice') }}
              <input v-model.number="actualPurchasePrice" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-cyan-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/40" />
            </label>
            <label class="text-[#365773]">{{ t('results.card.actualSalePrice') }}
              <input v-model.number="actualSalePrice" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-cyan-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/40" />
            </label>
            <label class="text-[#365773]">{{ t('results.card.actualPlatformFee') }}
              <input v-model.number="actualPlatformFee" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-cyan-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/40" />
            </label>
            <label class="text-[#365773]">{{ t('results.card.actualShippingCost') }}
              <input v-model.number="actualShippingCost" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-cyan-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/40" />
            </label>
            <label class="col-span-2 text-[#365773]">{{ t('results.card.actualOtherCost') }}
              <input v-model.number="actualOtherCost" type="number" min="0" step="0.01" class="mt-1 min-h-10 w-full rounded-md border border-cyan-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/40" />
            </label>
            <label class="col-span-2 text-[#365773]">{{ t('results.card.inventoryNotes') }}
              <textarea v-model="inventoryNotes" rows="2" class="mt-1 w-full rounded-md border border-cyan-200 bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/40" />
            </label>
          </div>
          <div class="flex items-end justify-between border-t border-cyan-200/70 pt-3">
            <div>
              <p class="text-[10px] uppercase tracking-wider text-cyan-800">{{ t('results.card.actualProfit') }}</p>
              <p v-if="actualProfit !== null" class="text-xl font-black" :class="actualProfit >= 0 ? 'text-emerald-700' : 'text-rose-700'">¥{{ actualProfit.toFixed(2) }}</p>
              <p v-else class="text-sm font-semibold text-cyan-900/60">{{ t('results.card.actualProfitPending') }}</p>
            </div>
            <p v-if="actualMargin !== null" class="text-xs text-[#52738b]">{{ t('results.card.margin') }} {{ actualMargin.toFixed(1) }}%</p>
          </div>
          <button type="button" class="inline-flex min-h-9 w-full items-center justify-center gap-2 rounded-md bg-cyan-800 px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-cyan-900 disabled:cursor-not-allowed disabled:opacity-60" :disabled="isSavingInventory || !props.filename || !info.商品ID" @click="handleSaveInventory">
            <Save class="h-3.5 w-3.5" aria-hidden="true" />
            {{ isSavingInventory ? t('results.card.savingInventory') : inventorySaved ? t('results.card.updateInventory') : t('results.card.saveInventory') }}
          </button>
          <p v-if="inventoryError" class="text-xs font-medium text-rose-700" role="alert">{{ t('results.card.saveInventoryFailed') }}</p>
        </div>
      </details>
    </CardContent>

    <CardFooter class="flex items-center justify-between gap-3 border-t border-[#d8ebf7] bg-[#eef8fd] px-4 py-3 text-[11px]">
      <div class="flex min-w-0 items-center gap-3 text-[#52738b]">
        <div class="flex items-center gap-1">
          <User class="w-3 h-3" />
          <span class="max-w-[110px] truncate">{{ seller.卖家昵称 || info.卖家昵称 || t('results.card.anonymous') }}</span>
        </div>
        <div class="flex items-center gap-1">
          <Clock class="w-3 h-3" />
          <span>{{ crawlTime }}</span>
        </div>
      </div>
      <a :href="info.商品链接" target="_blank" rel="noopener noreferrer" class="inline-flex min-h-8 shrink-0 items-center gap-1 font-semibold text-primary transition-[gap,color] hover:gap-1.5 hover:text-primary/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
        {{ t('results.card.detail') }} <ExternalLink class="w-3 h-3" />
      </a>
    </CardFooter>
  </Card>
</template>
