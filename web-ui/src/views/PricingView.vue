<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getProductPricing, type LocalizedText, type ProductPlan, type ProductPricing } from '@/api/settings'
import { Check, CircleDollarSign, Cpu, ExternalLink, Laptop, RefreshCw, ShieldCheck, Sparkles, Wrench } from 'lucide-vue-next'

const { locale, t } = useI18n()
const router = useRouter()
const pricing = ref<ProductPricing | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const language = computed<'zh' | 'en'>(() => locale.value === 'zh-CN' ? 'zh' : 'en')
const softwarePlans = computed(() => pricing.value?.plans.filter((plan) => plan.kind === 'software') ?? [])
const servicePlan = computed(() => pricing.value?.plans.find((plan) => plan.kind === 'service') ?? null)

function text(value: LocalizedText): string {
  return value[language.value]
}

function price(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: Number.isInteger(value) ? 0 : 1,
    maximumFractionDigits: 1,
  }).format(value)
}

function billingPeriod(plan: ProductPlan): string {
  return t('pricing.period.' + plan.billing_period)
}

function planNote(plan: ProductPlan): string {
  if (plan.id === 'professional_annual') return t('pricing.professionalNote')
  if (plan.id === 'remote_setup') return t('pricing.setupNote')
  return text(plan.note)
}

function choosePlan(plan: ProductPlan) {
  if (plan.availability !== 'available') return
  router.push({ name: 'License', query: { plan: plan.id } })
}

async function loadPricing() {
  isLoading.value = true
  error.value = null
  try {
    pricing.value = await getProductPricing()
  } catch (cause) {
    error.value = (cause as Error).message || t('pricing.loadFailed')
  } finally {
    isLoading.value = false
  }
}

onMounted(loadPricing)
</script>

<template>
  <div class="pricing-page page-shell relative space-y-5 overflow-hidden rounded-[28px] p-1.5 sm:p-2">
    <section class="pricing-hero relative overflow-hidden rounded-2xl border border-slate-700/70 p-5 text-white shadow-[0_22px_60px_-28px_rgba(15,23,42,0.78)] sm:p-7">
      <div class="pricing-radar-orbit pricing-radar-orbit-one" aria-hidden="true" />
      <div class="pricing-radar-orbit pricing-radar-orbit-two" aria-hidden="true" />
      <div class="relative grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
        <div>
          <div class="inline-flex items-center gap-2 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-xs font-bold tracking-wide text-lime-200">
            <CircleDollarSign class="h-3.5 w-3.5" aria-hidden="true" />
            {{ t('pricing.eyebrow') }}
          </div>
          <h1 class="mt-4 max-w-3xl text-3xl font-black tracking-tight sm:text-4xl">{{ pricing ? text(pricing.positioning) : t('pricing.title') }}</h1>
          <p class="mt-3 max-w-2xl text-sm leading-6 text-white/70">{{ t('pricing.description') }}</p>
        </div>
        <div class="rounded-2xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur-sm">
          <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-cyan-200">{{ t('pricing.heroCardTitle') }}</p>
          <p class="mt-2 text-lg font-black text-white">{{ t('pricing.heroCardValue') }}</p>
          <p class="mt-2 text-sm leading-6 text-white/65">{{ t('pricing.heroCardDescription') }}</p>
        </div>
      </div>
    </section>

    <div v-if="isLoading" class="grid gap-4 md:grid-cols-2 xl:grid-cols-4" aria-live="polite">
      <div v-for="index in 4" :key="index" class="h-[320px] animate-pulse rounded-2xl border border-[#c8e3f3] bg-white/80" />
    </div>

    <div v-else-if="error" class="app-alert-error flex flex-wrap items-center justify-between gap-3" role="alert">
      <span>{{ error }}</span>
      <Button variant="outline" size="sm" @click="loadPricing"><RefreshCw class="h-3.5 w-3.5" />{{ t('common.refresh') }}</Button>
    </div>

    <template v-else-if="pricing">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 class="text-xl font-black text-[#163b57]">{{ t('pricing.plansTitle') }}</h2>
          <p class="mt-1 text-sm text-[#52738b]">{{ t('pricing.plansDescription') }}</p>
        </div>
        <span class="text-xs font-semibold text-[#52738b]">{{ t('pricing.purchaseHint') }}</span>
      </div>
      <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card
          v-for="plan in softwarePlans"
          :key="plan.id"
          class="pricing-plan relative flex h-full flex-col overflow-hidden border-none"
          :class="[
            plan.recommended ? 'pricing-plan-featured' : '',
            plan.availability === 'coming_soon' ? 'pricing-plan-upcoming' : '',
          ]"
        >
          <div v-if="plan.recommended" class="absolute right-0 top-0 rounded-bl-xl bg-[var(--brand-lime)] px-3 py-1 text-[10px] font-black tracking-[0.12em] text-[var(--brand-deep)]">
            {{ t('pricing.recommended') }}
          </div>
          <CardHeader class="pb-4">
            <div class="flex items-center justify-between gap-3">
              <Badge variant="outline" class="border-cyan-200 bg-cyan-50 text-cyan-800">{{ text(plan.badge) }}</Badge>
              <span v-if="plan.availability === 'coming_soon'" class="text-xs font-bold text-amber-700">{{ t('pricing.comingSoon') }}</span>
            </div>
            <CardTitle class="mt-4 text-xl text-[#163b57]">{{ text(plan.name) }}</CardTitle>
            <CardDescription class="mt-2 min-h-11 leading-5 text-[#52738b]">{{ text(plan.description) }}</CardDescription>
          </CardHeader>
          <CardContent class="flex flex-1 flex-col">
            <div class="flex items-end gap-1">
              <span class="font-mono text-4xl font-black tracking-[-0.06em] text-[#163b57]">{{ price(plan.price) }}</span>
              <span class="mb-1 text-sm font-semibold text-[#52738b]">/ {{ billingPeriod(plan) }}</span>
            </div>
            <ul class="mt-5 space-y-3">
              <li v-for="feature in plan.features" :key="text(feature)" class="flex items-start gap-2 text-sm leading-5 text-[#365773]">
                <Check class="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden="true" />
                <span>{{ text(feature) }}</span>
              </li>
            </ul>
            <div class="mt-auto pt-5">
              <p class="rounded-xl border border-[#d8ebf7] bg-[#f4fbff] px-3 py-2.5 text-xs leading-5 text-[#52738b]">{{ planNote(plan) }}</p>
              <Button
                v-if="plan.availability === 'available'"
                class="mt-3 w-full"
                :variant="plan.recommended ? 'default' : 'outline'"
                @click="choosePlan(plan)"
              >
                {{ t('pricing.choosePlan') }}
              </Button>
              <div v-if="plan.availability === 'coming_soon'" class="mt-3 inline-flex items-center gap-2 text-xs font-semibold text-amber-700">
                <Sparkles class="h-3.5 w-3.5" aria-hidden="true" />
                {{ t('pricing.notForSaleYet') }}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section class="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
        <Card v-if="servicePlan" class="pricing-service overflow-hidden border-none">
          <CardHeader class="border-b border-amber-100 bg-amber-50">
            <div class="flex items-start gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-200/70 text-amber-800"><Wrench class="h-5 w-5" aria-hidden="true" /></span>
              <div>
                <CardTitle class="text-[#5f3b11]">{{ text(servicePlan.name) }}</CardTitle>
                <CardDescription class="mt-1 text-amber-900/65">{{ text(servicePlan.description) }}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent class="pt-5">
            <p class="font-mono text-3xl font-black tracking-[-0.06em] text-[#5f3b11]">{{ price(servicePlan.price) }} <span class="text-sm font-semibold">/ {{ billingPeriod(servicePlan) }}</span></p>
            <ul class="mt-4 space-y-3">
              <li v-for="feature in servicePlan.features" :key="text(feature)" class="flex items-start gap-2 text-sm leading-5 text-amber-950/75">
                <Check class="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />
                <span>{{ text(feature) }}</span>
              </li>
            </ul>
            <p class="mt-4 rounded-xl border border-amber-200 bg-white/75 p-3 text-xs leading-5 text-amber-900/70">{{ planNote(servicePlan) }}</p>
          </CardContent>
        </Card>

        <Card class="command-panel overflow-hidden border-none">
          <CardHeader class="border-b border-[#d8ebf7] bg-[#eaf7ff]">
            <div class="flex items-start gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-100 text-cyan-800"><ShieldCheck class="h-5 w-5" aria-hidden="true" /></span>
              <div>
                <CardTitle class="text-[#163b57]">{{ t('pricing.boundariesTitle') }}</CardTitle>
                <CardDescription class="mt-1 text-[#52738b]">{{ t('pricing.boundariesDescription') }}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent class="grid gap-3 pt-5 sm:grid-cols-2">
            <div v-for="(policy, key) in pricing.policies" :key="key" class="rounded-xl border border-[#d8ebf7] bg-[#fbfeff] p-3.5">
              <div class="flex items-center gap-2">
                <Cpu v-if="key === 'api_cost'" class="h-4 w-4 text-cyan-700" aria-hidden="true" />
                <Laptop v-else-if="key === 'license'" class="h-4 w-4 text-cyan-700" aria-hidden="true" />
                <ExternalLink v-else class="h-4 w-4 text-cyan-700" aria-hidden="true" />
                <p class="text-sm font-bold text-[#163b57]">{{ t('pricing.policyLabels.' + key) }}</p>
              </div>
              <p class="mt-2 text-sm leading-5 text-[#52738b]">{{ text(policy) }}</p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section class="rounded-2xl border border-cyan-200/80 bg-cyan-50/70 p-4 text-sm leading-6 text-cyan-950 sm:p-5">
        <div class="flex items-start gap-3">
          <ShieldCheck class="mt-0.5 h-5 w-5 shrink-0 text-cyan-700" aria-hidden="true" />
          <div>
            <p class="font-bold">{{ t('pricing.trustTitle') }}</p>
            <p class="mt-1 text-cyan-900/75">{{ t('pricing.trustDescription') }}</p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
