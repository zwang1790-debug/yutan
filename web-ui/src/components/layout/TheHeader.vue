<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import DashboardTaskSearch from '@/components/layout/DashboardTaskSearch.vue'
import BrandMark from '@/components/layout/BrandMark.vue'
import LocaleToggle from '@/components/layout/LocaleToggle.vue'
import AccountSecurityDialog from '@/components/layout/AccountSecurityDialog.vue'
import { 
  Bell, 
  Search, 
  UserCircle,
  HelpCircle,
  Menu,
} from 'lucide-vue-next'
import Badge from '@/components/ui/badge/Badge.vue'
import { useMobileNav } from '@/composables/useMobileNav'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const route = useRoute()
const { toggleMobileNav } = useMobileNav()
const isAccountDialogOpen = ref(false)
const { t } = useI18n()

const isDashboard = computed(() => route.name === 'Dashboard')

function goNotifications() {
  router.push({ name: 'Settings', query: { tab: 'notifications' } })
}

function goPrompts() {
  router.push({ name: 'Settings', query: { tab: 'prompts' } })
}

</script>

<template>
  <header class="flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur-md sm:px-6">
    <!-- Brand Logo -->
    <RouterLink
      to="/dashboard"
      class="group flex items-center gap-2 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      :aria-label="t('header.goHome')"
    >
      <BrandMark :size="40" />
      <div class="min-w-0 leading-none">
        <h1 class="truncate text-[17px] font-black tracking-[-0.03em] text-slate-950">
          {{ t('app.name') }}
        </h1>
        <p class="mt-1 hidden truncate text-[10px] font-semibold tracking-[0.08em] text-slate-400 sm:block">
          {{ t('app.tagline') }}
        </p>
      </div>
      <Badge variant="outline" class="ml-1 hidden border-primary/20 bg-primary/5 text-[10px] font-bold uppercase tracking-widest text-primary sm:flex">
        {{ t('app.mode') }}
      </Badge>
    </RouterLink>

    <!-- Search & Navigation -->
    <div class="mx-6 hidden max-w-md flex-1 md:flex">
      <DashboardTaskSearch v-if="isDashboard" />
      <div v-else class="flex h-10 w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-400" :aria-label="t('header.searchUnavailable')">
        <span class="flex min-w-0 items-center gap-2">
          <Search class="h-4 w-4 shrink-0" aria-hidden="true" />
          <span class="truncate">{{ t('header.searchUnavailable') }}</span>
        </span>
        <span class="shrink-0 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-300">{{ t('header.searchUnavailableBadge') }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <LocaleToggle />
      </div>

      <div class="flex items-center gap-1 sm:gap-2">
         <Button
           variant="ghost"
           size="icon"
           class="rounded-full text-slate-500 hover:text-primary hover:bg-primary/10"
           :aria-label="t('header.openNotifications')"
           @click="goNotifications"
         >
            <Bell class="w-5 h-5" />
         </Button>
         <Button
           variant="ghost"
           size="icon"
           class="rounded-full text-slate-500 hover:text-primary hover:bg-primary/10"
           :aria-label="t('header.openPrompts')"
           @click="goPrompts"
         >
            <HelpCircle class="w-5 h-5" />
         </Button>
      </div>
      
      <div class="h-6 w-px bg-slate-200 mx-1 hidden sm:block"></div>

      <Button 
        variant="ghost" 
        class="flex items-center gap-2 rounded-full px-2 transition-all hover:bg-slate-100 active:scale-95 sm:pl-2 sm:pr-4"
        :aria-label="t('header.accountSecurity')"
        :title="t('header.accountSecurity')"
        @click="isAccountDialogOpen = true"
      >
        <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center overflow-hidden border border-slate-300 shadow-sm">
           <UserCircle class="w-6 h-6 text-slate-500" />
        </div>
        <div class="hidden text-left lg:block">
           <p class="text-xs font-black text-slate-700 leading-none mb-0.5">{{ t('app.workspace') }}</p>
           <p class="text-[10px] text-slate-400 font-medium">{{ t('header.accountSecurity') }}</p>
        </div>
      </Button>

      <Button
        variant="ghost"
        size="icon"
        class="md:hidden"
        :aria-label="t('header.openNavigation')"
        @click="toggleMobileNav"
      >
         <Menu class="w-6 h-6 text-slate-700" />
      </Button>
    </div>
  </header>
  <AccountSecurityDialog v-model:open="isAccountDialogOpen" />
</template>
