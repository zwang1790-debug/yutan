<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import TheHeader from '@/components/layout/TheHeader.vue'
import TheSidebar from '@/components/layout/TheSidebar.vue'
import { useMobileNav } from '@/composables/useMobileNav'
import SetupWizard from '@/components/layout/SetupWizard.vue'

const { isMobileNavOpen, closeMobileNav } = useMobileNav()
const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const showSetupBanner = ref(localStorage.getItem('setupWizardCompleted') !== 'true')
const showSetupWizard = ref(localStorage.getItem('setupWizardCompleted') !== 'true')

function openSetupWizard() {
  showSetupWizard.value = true
}

watch(
  () => route.query.wizard,
  (value) => {
    if (value !== '1') return
    openSetupWizard()
    const query = { ...route.query }
    delete query.wizard
    router.replace({ query })
  },
  { immediate: true },
)

function handleWizardCompleted() {
  showSetupWizard.value = false
  showSetupBanner.value = false
}
</script>

<template>
  <div class="relative flex min-h-screen w-full flex-col bg-background selection:bg-primary/15">
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[120] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary-foreground"
    >
      {{ t('common.skipToContent') }}
    </a>

    <!-- Header -->
    <TheHeader class="sticky top-0 z-50" />

    <transition name="mobile-nav">
      <div v-if="isMobileNavOpen" class="fixed inset-0 z-[90] md:hidden">
        <button
          type="button"
          class="absolute inset-0 bg-slate-950/25 backdrop-blur-[2px]"
          :aria-label="t('common.close')"
          @click="closeMobileNav"
        />
        <aside class="relative h-full w-72 border-r border-slate-200 bg-white p-4 shadow-2xl">
          <TheSidebar class="max-h-full overflow-y-auto pt-4" @navigate="closeMobileNav" />
        </aside>
      </div>
    </transition>

    <div class="flex flex-grow relative z-10">
      <!-- Sidebar -->
      <aside class="hidden w-[228px] flex-shrink-0 border-r border-slate-200 bg-white md:block">
        <TheSidebar class="sticky top-16 h-[calc(100vh-4rem)] max-h-[calc(100vh-4rem)] overflow-y-auto px-3 py-5" />
      </aside>

      <!-- Main Content Area -->
      <main id="main-content" tabindex="-1" class="flex-grow overflow-x-hidden px-4 py-5 focus:outline-none sm:px-6 md:px-8 md:py-7">
        <div class="page-shell animate-fade-in">
          <div v-if="showSetupBanner" class="mb-6 flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50/90 px-5 py-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="font-semibold text-amber-900">先完成 3 步配置，再开始监控</p>
              <p class="mt-1 text-sm text-amber-800/80">配置 AI、确认闲鱼登录态，并运行一次本地环境诊断。</p>
            </div>
            <div class="flex shrink-0 gap-2">
              <button type="button" class="inline-flex items-center justify-center rounded-lg bg-amber-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-amber-800" @click="openSetupWizard">打开配置向导</button>
              <button type="button" class="rounded-lg px-3 py-2 text-sm text-amber-900/70 hover:bg-amber-100" @click="showSetupBanner = false">稍后</button>
            </div>
          </div>
          <RouterView v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </RouterView>
        </div>
      </main>
    </div>
    <SetupWizard v-model:open="showSetupWizard" @completed="handleWizardCompleted" />
  </div>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.mobile-nav-enter-active,
.mobile-nav-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.mobile-nav-enter-from,
.mobile-nav-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

@media (prefers-reduced-motion: reduce) {
  .page-enter-active,
  .page-leave-active,
  .mobile-nav-enter-active,
  .mobile-nav-leave-active {
    transition: none;
  }

  .page-enter-from,
  .page-leave-to,
  .mobile-nav-enter-from,
  .mobile-nav-leave-to {
    opacity: 1;
    transform: none;
  }
}
</style>
