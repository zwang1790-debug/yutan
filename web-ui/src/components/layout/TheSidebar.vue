<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { 
  LayoutDashboard, 
  ListTodo, 
  Users, 
  Layers, 
  Terminal, 
  Settings2,
  CircleDollarSign,
  ShieldCheck,
  ChevronRight
} from 'lucide-vue-next'
import { useWebSocket } from '@/composables/useWebSocket'
import { useI18n } from 'vue-i18n'

const emit = defineEmits<{
  (event: 'navigate'): void
}>()
const { isConnected } = useWebSocket()
const { t } = useI18n()

const navItems = computed(() => [
  { to: '/dashboard', label: t('sidebar.dashboard'), icon: LayoutDashboard },
  { to: '/tasks', label: t('sidebar.tasks'), icon: ListTodo },
  { to: '/accounts', label: t('sidebar.accounts'), icon: Users },
  { to: '/results', label: t('sidebar.results'), icon: Layers },
  { to: '/logs', label: t('sidebar.logs'), icon: Terminal },
  { to: '/settings', label: t('sidebar.settings'), icon: Settings2 },
])
const commercialItems = computed(() => [
  { to: '/pricing', label: t('sidebar.pricing'), icon: CircleDollarSign },
  { to: '/license', label: t('sidebar.license'), icon: ShieldCheck },
])

const connectionLabel = computed(() => (
  isConnected.value ? t('sidebar.backendConnected') : t('sidebar.backendConnecting')
))
const connectionTone = computed(() =>
  isConnected.value
    ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
    : 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.45)]'
)
</script>

<template>
  <nav class="max-h-full space-y-1 overflow-y-auto overscroll-contain pr-1">
    <RouterLink
      v-for="item in navItems"
      :key="item.to"
      :to="item.to"
      v-slot="{ isActive }"
      class="group relative flex min-h-11 items-center rounded-xl px-2 py-1.5 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
      @click="emit('navigate')"
    >
      <div
        class="relative z-10 flex w-full items-center rounded-lg px-3.5 py-2.5"
        :class="isActive ? 'border-l-2 border-primary bg-blue-50 text-slate-950' : 'border-l-2 border-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
      >
        <component 
          :is="item.icon" 
          class="w-5 h-5 mr-3 transition-colors"
          :class="isActive ? 'text-primary' : 'text-slate-400 group-hover:text-slate-600'"
        />
        <span 
          class="flex-grow text-sm font-semibold transition-colors"
          :class="isActive ? 'text-slate-950' : 'text-slate-600 group-hover:text-slate-800'"
        >
          {{ item.label }}
        </span>
        <ChevronRight 
          v-if="isActive"
          class="h-4 w-4 text-primary"
        />
      </div>
    </RouterLink>

    <div class="mt-4 border-t border-slate-200 pt-4">
      <p class="px-3.5 pb-2 text-[10px] font-black uppercase tracking-[0.16em] text-slate-400">
        {{ t('sidebar.commercial') }}
      </p>
      <RouterLink
        v-for="item in commercialItems"
        :key="item.to"
        :to="item.to"
        v-slot="{ isActive }"
        class="group relative flex min-h-11 items-center rounded-xl px-2 py-1.5 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
        @click="emit('navigate')"
      >
        <div
          class="relative z-10 flex w-full items-center rounded-lg px-3.5 py-2.5"
          :class="isActive ? 'border-l-2 border-primary bg-blue-50 text-slate-950' : 'border-l-2 border-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-800'"
        >
          <component
            :is="item.icon"
            class="mr-3 h-5 w-5 transition-colors"
            :class="isActive ? 'text-primary' : 'text-slate-400 group-hover:text-slate-600'"
          />
          <span
            class="flex-grow text-sm font-semibold transition-colors"
            :class="isActive ? 'text-slate-950' : 'text-slate-600 group-hover:text-slate-800'"
          >
            {{ item.label }}
          </span>
          <ChevronRight
            v-if="isActive"
            class="h-4 w-4 text-primary"
          />
        </div>
      </RouterLink>
    </div>

    <!-- Support Section -->
    <div class="mt-8 px-1">
      <div class="rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-3">
         <p class="eyebrow mb-2">{{ t('sidebar.systemStatus') }}</p>
         <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full" :class="connectionTone"></div>
            <span class="text-xs font-semibold text-slate-600">{{ connectionLabel }}</span>
         </div>
      </div>
    </div>
  </nav>
</template>
