<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { AlertTriangle, CheckCircle2, Circle, ExternalLink, RefreshCw, ShieldCheck } from 'lucide-vue-next'
import { getDiagnostics, getLoginStateStatus, getSystemStatus, type DiagnosticsResponse, type LoginStateStatus, type SystemStatus } from '@/api/settings'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [value: boolean]; completed: [] }>()
const router = useRouter()

const step = ref(0)
const isLoading = ref(false)
const error = ref('')
const systemStatus = ref<SystemStatus | null>(null)
const loginState = ref<LoginStateStatus | null>(null)
const diagnostics = ref<DiagnosticsResponse | null>(null)

const steps = [
  { title: 'AI 配置', description: '让系统可以分析商品和估算利润。' },
  { title: '闲鱼登录态', description: '确认采集任务使用的登录态有效。' },
  { title: '本地诊断', description: '检查数据目录、运行环境和关键依赖。' },
]

const aiReady = computed(() => systemStatus.value?.ai_configured === true)
const loginReady = computed(() => loginState.value?.exists === true && loginState.value?.valid_json === true)
const diagnosticsReady = computed(() => diagnostics.value?.success === true)
const allReady = computed(() => aiReady.value && loginReady.value && diagnosticsReady.value)

function close() {
  emit('update:open', false)
}

function finish() {
  localStorage.setItem('setupWizardCompleted', 'true')
  emit('completed')
  close()
}

function skip() {
  localStorage.setItem('setupWizardCompleted', 'true')
  emit('completed')
  close()
}

async function refresh() {
  isLoading.value = true
  error.value = ''
  try {
    const [status, login, diagnostic] = await Promise.all([
      getSystemStatus(),
      getLoginStateStatus(),
      getDiagnostics(),
    ])
    systemStatus.value = status
    loginState.value = login
    diagnostics.value = diagnostic
  } catch (err) {
    error.value = err instanceof Error ? err.message : '读取配置状态失败'
  } finally {
    isLoading.value = false
  }
}

function openSettings() {
  close()
  router.push({ path: '/settings', query: { tab: 'ai' } })
}

function openAccounts() {
  close()
  router.push('/accounts')
}

function statusFor(index: number) {
  if (index === 0) return aiReady.value
  if (index === 1) return loginReady.value
  return diagnosticsReady.value
}

onMounted(refresh)
</script>

<template>
  <Dialog :open="props.open" @update:open="emit('update:open', $event)">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <ShieldCheck class="h-5 w-5 text-primary" />
          首次启动配置向导
        </DialogTitle>
        <DialogDescription>用 3 步确认本地环境已经具备稳定运行监控任务的条件。</DialogDescription>
      </DialogHeader>

      <div class="grid gap-6 md:grid-cols-[180px_1fr]">
        <div class="space-y-2">
          <button
            v-for="(item, index) in steps"
            :key="item.title"
            type="button"
            class="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition"
            :class="step === index ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted'"
            @click="step = index"
          >
            <CheckCircle2 v-if="statusFor(index)" class="h-4 w-4 text-emerald-600" />
            <Circle v-else class="h-4 w-4" />
            <span>{{ index + 1 }}. {{ item.title }}</span>
          </button>
        </div>

        <div class="min-h-[210px] rounded-2xl border bg-muted/20 p-5">
          <template v-if="step === 0">
            <h3 class="font-semibold">配置 AI 分析</h3>
            <p class="mt-2 text-sm text-muted-foreground">AI 用于判断商品质量、风险和预估利润。建议先在设置页保存并测试 API。</p>
            <div class="mt-5 flex items-center gap-2 text-sm">
              <CheckCircle2 v-if="aiReady" class="h-4 w-4 text-emerald-600" />
              <AlertTriangle v-else class="h-4 w-4 text-amber-600" />
              <span>{{ aiReady ? 'AI 配置已完成' : '尚未检测到可用的 AI 配置' }}</span>
            </div>
            <Button class="mt-5" variant="outline" @click="openSettings">前往 AI 设置 <ExternalLink class="ml-2 h-4 w-4" /></Button>
          </template>

          <template v-else-if="step === 1">
            <h3 class="font-semibold">确认闲鱼登录态</h3>
            <p class="mt-2 text-sm text-muted-foreground">登录态只保存在本机，用于执行采集。不要把包含登录态的备份文件发送给他人。</p>
            <div class="mt-5 flex items-center gap-2 text-sm">
              <CheckCircle2 v-if="loginReady" class="h-4 w-4 text-emerald-600" />
              <AlertTriangle v-else class="h-4 w-4 text-amber-600" />
              <span>{{ loginReady ? '登录态文件存在且 JSON 有效' : '尚未检测到有效登录态' }}</span>
            </div>
            <Button class="mt-5" variant="outline" @click="openAccounts">前往账号管理 <ExternalLink class="ml-2 h-4 w-4" /></Button>
          </template>

          <template v-else>
            <h3 class="font-semibold">运行本地诊断</h3>
            <p class="mt-2 text-sm text-muted-foreground">诊断会检查关键目录、配置文件和运行依赖，不会修改你的任务数据。</p>
            <div class="mt-5 flex items-center gap-2 text-sm">
              <CheckCircle2 v-if="diagnosticsReady" class="h-4 w-4 text-emerald-600" />
              <AlertTriangle v-else class="h-4 w-4 text-amber-600" />
              <span>{{ diagnostics?.summary || '尚未完成诊断' }}</span>
            </div>
            <Button class="mt-5" variant="outline" :disabled="isLoading" @click="refresh">
              <RefreshCw class="mr-2 h-4 w-4" :class="isLoading ? 'animate-spin' : ''" />
              {{ isLoading ? '检测中...' : '重新检测' }}
            </Button>
          </template>

          <p v-if="error" class="mt-4 text-sm text-destructive">{{ error }}</p>
        </div>
      </div>

      <DialogFooter class="flex-col-reverse gap-2 sm:flex-row sm:justify-between">
        <Button variant="ghost" @click="skip">跳过，稍后配置</Button>
        <div class="flex gap-2">
          <Button v-if="step > 0" variant="outline" @click="step -= 1">上一步</Button>
          <Button v-if="step < steps.length - 1" @click="step += 1">下一步</Button>
          <Button v-else :disabled="!allReady" @click="finish">完成向导</Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
