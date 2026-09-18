<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { listAccounts, getAccount, createAccount, updateAccount, deleteAccount, type AccountItem } from '@/api/accounts'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from '@/components/ui/toast'
import { ArrowUpRight, Check, ClipboardList, Copy, UserRound, Search, RefreshCw, ShieldCheck, Plus, ArrowRight } from 'lucide-vue-next'
import { openExternalUrl } from '@/api/system'
const { t } = useI18n()

const accounts = ref<AccountItem[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const router = useRouter()

const isCreateDialogOpen = ref(false)
const isEditDialogOpen = ref(false)
const isDeleteDialogOpen = ref(false)

const newName = ref('')
const newContent = ref('')
const editName = ref('')
const editContent = ref('')
const deleteName = ref('')
const searchQuery = ref('')
const copiedGuideLink = ref('')
const extensionUrl = 'https://chromewebstore.google.com/detail/xianyu-login-state-extrac/eidlpfjiodpigmfcahkmlenhppfklcoa'
const goofishUrl = 'https://www.goofish.com'

const guideSteps = computed(() => [
  {
    id: 'extension',
    text: t('accounts.cookieGuide.step1Prefix'),
    link: t('accounts.cookieGuide.extension'),
    href: extensionUrl,
    copyable: true,
  },
  {
    id: 'website',
    text: t('accounts.cookieGuide.step2Prefix'),
    link: t('accounts.cookieGuide.website'),
    href: goofishUrl,
    copyable: false,
  },
  { id: 'extract', text: t('accounts.cookieGuide.step3'), link: '', href: '', copyable: false },
  { id: 'paste', text: t('accounts.cookieGuide.step4'), link: '', href: '', copyable: false },
  { id: 'multi-account', text: t('accounts.cookieGuide.step5'), link: '', href: '', copyable: false },
])

const filteredAccounts = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase()
  if (!query) return accounts.value
  return accounts.value.filter((account) => `${account.name} ${account.path}`.toLocaleLowerCase().includes(query))
})

async function openGuideLink(href: string) {
  try {
    await openExternalUrl(href)
    toast({ title: t('accounts.toasts.externalOpened') })
  } catch (error) {
    toast({ title: t('accounts.toasts.externalOpenFailed'), description: (error as Error).message, variant: 'destructive' })
  }
}

async function copyGuideLink(href: string) {
  if (!navigator.clipboard) {
    toast({ title: t('accounts.toasts.copyLinkFailed'), description: href, variant: 'destructive' })
    return
  }
  try {
    await navigator.clipboard.writeText(href)
    copiedGuideLink.value = href
    toast({ title: t('accounts.toasts.linkCopied') })
    window.setTimeout(() => {
      if (copiedGuideLink.value === href) copiedGuideLink.value = ''
    }, 1800)
  } catch (error) {
    toast({ title: t('accounts.toasts.copyLinkFailed'), description: (error as Error).message, variant: 'destructive' })
  }
}

async function refreshAccounts() {
  await fetchAccounts()
}

async function fetchAccounts() {
  isLoading.value = true
  try {
    accounts.value = await listAccounts()
  } catch (e) {
    toast({ title: t('accounts.toasts.loadFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isLoading.value = false
  }
}

function openCreateDialog() {
  newName.value = ''
  newContent.value = ''
  isCreateDialogOpen.value = true
}

async function openEditDialog(name: string) {
  isSaving.value = true
  try {
    const detail = await getAccount(name)
    editName.value = detail.name
    editContent.value = detail.content
    isEditDialogOpen.value = true
  } catch (e) {
    toast({ title: t('accounts.toasts.loadContentFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

function openDeleteDialog(name: string) {
  deleteName.value = name
  isDeleteDialogOpen.value = true
}

function goCreateTask(name: string) {
  router.push({ path: '/tasks', query: { account: name, create: '1' } })
}

async function handleCreateAccount() {
  if (!newName.value.trim() || !newContent.value.trim()) {
    toast({ title: t('accounts.toasts.incomplete'), description: t('accounts.toasts.createDescriptionRequired'), variant: 'destructive' })
    return
  }
  isSaving.value = true
  try {
    await createAccount({ name: newName.value.trim(), content: newContent.value.trim() })
    toast({ title: t('accounts.toasts.created') })
    isCreateDialogOpen.value = false
    await fetchAccounts()
  } catch (e) {
    toast({ title: t('accounts.toasts.createFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

async function handleUpdateAccount() {
  if (!editContent.value.trim()) {
    toast({ title: t('accounts.toasts.contentRequired'), description: t('accounts.toasts.updateDescriptionRequired'), variant: 'destructive' })
    return
  }
  isSaving.value = true
  try {
    await updateAccount(editName.value, editContent.value.trim())
    toast({ title: t('accounts.toasts.updated') })
    isEditDialogOpen.value = false
    await fetchAccounts()
  } catch (e) {
    toast({ title: t('accounts.toasts.updateFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteAccount() {
  isSaving.value = true
  try {
    await deleteAccount(deleteName.value)
    toast({ title: t('accounts.toasts.deleted') })
    isDeleteDialogOpen.value = false
    await fetchAccounts()
  } catch (e) {
    toast({ title: t('accounts.toasts.deleteFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

onMounted(fetchAccounts)
</script>

<template>
  <div class="accounts-page page-shell relative space-y-5 overflow-hidden rounded-[28px] p-1.5 sm:p-2">
    <div class="command-hero flex flex-col gap-5 p-5 sm:flex-row sm:items-end sm:justify-between sm:p-6">
      <div>
        <div class="flex items-center gap-3">
          <span class="flex size-11 items-center justify-center rounded-2xl bg-[var(--brand-lime)] text-[var(--brand-deep)] shadow-lg shadow-black/10">
            <UserRound class="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p class="eyebrow text-[var(--brand-lime)]">{{ t('accounts.eyebrow') }}</p>
            <h1 class="mt-1 text-2xl font-black tracking-tight text-white sm:text-3xl">{{ t('accounts.title') }}</h1>
          </div>
        </div>
        <p class="mt-4 max-w-2xl text-sm leading-6 text-white/65">{{ t('accounts.description') }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2 sm:justify-end">
        <span class="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-xs font-semibold text-emerald-200">
          <ShieldCheck class="h-3.5 w-3.5" aria-hidden="true" />
          {{ t('accounts.count', { count: accounts.length }) }}
        </span>
        <Button variant="outline" size="sm" class="border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white" :disabled="isLoading" :aria-label="t('common.refresh')" @click="refreshAccounts">
          <RefreshCw class="h-3.5 w-3.5" :class="isLoading ? 'animate-spin' : ''" />
          <span class="hidden sm:inline">{{ t('common.refresh') }}</span>
        </Button>
        <Button class="bg-[var(--brand-lime)] text-[var(--brand-deep)] hover:bg-lime-300" @click="openCreateDialog"><Plus class="h-4 w-4" />{{ t('accounts.add') }}</Button>
      </div>
    </div>

    <Card class="command-panel-dark overflow-hidden border-none">
      <CardHeader class="border-b border-white/10 bg-slate-950/70 text-white">
        <div class="flex items-start gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-300/15 text-cyan-200">
            <ClipboardList class="h-5 w-5" />
          </div>
          <div>
            <CardTitle>{{ t('accounts.cookieGuide.title') }}</CardTitle>
            <CardDescription class="mt-1 text-white/55">{{ t('accounts.guideDescription') }}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent class="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-5">
        <div v-for="(step, index) in guideSteps" :key="step.id" class="rounded-xl border border-white/10 bg-white/[0.06] p-4">
          <p class="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--brand-lime)]">{{ t('accounts.stepLabel', { count: index + 1 }) }}</p>
          <p class="mt-2 text-sm leading-6 text-white/70">
            <template v-if="step.link">
              {{ step.text }}
              <a class="font-semibold text-cyan-200 underline-offset-4 hover:underline" :href="step.href" @click.prevent="openGuideLink(step.href)">{{ step.link }}<ArrowUpRight class="ml-1 inline h-3.5 w-3.5" /></a>
            </template>
            <template v-else>{{ step.text }}</template>
          </p>
          <div v-if="step.copyable" class="mt-3 flex flex-wrap items-center gap-2">
            <button type="button" class="inline-flex min-h-8 items-center gap-1.5 rounded-md border border-cyan-200/20 bg-cyan-300/10 px-2.5 py-1.5 text-xs font-semibold text-cyan-100 transition-colors hover:bg-cyan-300/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-200/60" @click="copyGuideLink(step.href)">
              <Check v-if="copiedGuideLink === step.href" class="h-3.5 w-3.5 text-emerald-300" />
              <Copy v-else class="h-3.5 w-3.5" />
              {{ copiedGuideLink === step.href ? t('accounts.cookieGuide.linkCopied') : t('accounts.cookieGuide.copyLink') }}
            </button>
            <span class="text-[11px] leading-4 text-white/45">{{ t('accounts.cookieGuide.chromeHint') }}</span>
          </div>
        </div>
      </CardContent>
    </Card>

    <Card class="command-panel overflow-hidden border-none">
      <CardHeader class="border-b border-[#d8ebf7] bg-white px-4 py-4 sm:px-5">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle>{{ t('accounts.list.title') }}</CardTitle>
            <CardDescription>{{ t('accounts.list.description') }}</CardDescription>
          </div>
          <div class="relative w-full lg:max-w-sm">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#23789a]" aria-hidden="true" />
            <Input v-model="searchQuery" class="h-10 border-[#b9dced] bg-[#f3faff] pl-9 text-[#163b57] placeholder:text-[#6c879d] focus-visible:ring-[#14b8d4]" :placeholder="t('accounts.console.searchPlaceholder')" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div class="space-y-4 md:hidden">
          <div v-if="isLoading" class="py-10 text-center text-sm text-[#52738b]">{{ t('common.loading') }}</div>
          <div v-else-if="filteredAccounts.length === 0" class="py-10 text-center text-sm text-[#52738b]">{{ searchQuery ? t('accounts.console.noMatch') : t('accounts.list.empty') }}</div>
          <article
            v-else
            v-for="account in filteredAccounts"
            :key="account.name"
            class="app-surface-subtle border-[#c8e3f3] bg-[#fbfeff] p-4 transition-colors hover:border-cyan-300 hover:bg-[#f0fbff]"
          >
            <div class="space-y-2">
              <div class="flex items-center justify-between gap-3">
                <h3 class="truncate text-base font-bold text-[#163b57]">{{ account.name }}</h3>
                <Button size="sm" variant="outline" class="min-h-10" @click="goCreateTask(account.name)">{{ t('accounts.list.createTask') }}</Button>
              </div>
              <p class="break-all text-sm text-[#52738b]">{{ account.path }}</p>
            </div>
            <div class="mt-4 flex flex-wrap gap-2">
              <Button size="sm" variant="outline" class="min-h-10 min-w-[120px] flex-1" @click="openEditDialog(account.name)">{{ t('accounts.list.update') }}</Button>
              <Button size="sm" variant="destructive" class="min-h-10 min-w-[120px] flex-1" @click="openDeleteDialog(account.name)">{{ t('accounts.list.delete') }}</Button>
            </div>
          </article>
        </div>

        <div class="hidden md:block">
              <Table>
            <TableHeader class="border-b border-[#c8e3f3] bg-[#eaf7ff]">
              <TableRow>
                <TableHead>{{ t('accounts.list.name') }}</TableHead>
                <TableHead>{{ t('accounts.list.file') }}</TableHead>
                <TableHead class="text-right">{{ t('accounts.list.actions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-if="isLoading">
                <TableCell colspan="3" class="h-20 text-center text-[#52738b]">{{ t('common.loading') }}</TableCell>
              </TableRow>
              <TableRow v-else-if="filteredAccounts.length === 0">
                <TableCell colspan="3" class="h-20 text-center text-[#52738b]">{{ searchQuery ? t('accounts.console.noMatch') : t('accounts.list.empty') }}</TableCell>
              </TableRow>
               <TableRow v-else v-for="account in filteredAccounts" :key="account.name" class="border-b border-[#e1f0f7] transition-colors hover:bg-[#f0fbff]">
                 <TableCell class="font-bold text-[#163b57]">{{ account.name }}</TableCell>
                 <TableCell class="text-sm text-[#52738b]">{{ account.path }}</TableCell>
                <TableCell class="text-right">
                  <div class="flex justify-end gap-2">
                    <Button size="sm" variant="outline" class="border-cyan-200 text-cyan-700 hover:bg-cyan-50" @click="goCreateTask(account.name)"><ArrowRight class="h-3.5 w-3.5" />{{ t('accounts.list.createTask') }}</Button>
                    <Button size="sm" variant="outline" @click="openEditDialog(account.name)">{{ t('accounts.list.update') }}</Button>
                    <Button size="sm" variant="destructive" @click="openDeleteDialog(account.name)">{{ t('accounts.list.delete') }}</Button>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>

    <Dialog v-model:open="isCreateDialogOpen">
      <DialogContent class="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle>{{ t('accounts.createDialog.title') }}</DialogTitle>
          <DialogDescription>{{ t('accounts.createDialog.description') }}</DialogDescription>
        </DialogHeader>
        <div class="space-y-4">
          <div class="grid gap-2">
            <Label>{{ t('accounts.createDialog.name') }}</Label>
            <Input v-model="newName" :placeholder="t('accounts.createDialog.namePlaceholder')" />
          </div>
          <div class="grid gap-2">
            <Label>{{ t('accounts.createDialog.jsonContent') }}</Label>
            <Textarea v-model="newContent" class="min-h-[200px]" :placeholder="t('accounts.createDialog.jsonPlaceholder')" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isCreateDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button :disabled="isSaving" @click="handleCreateAccount">
            {{ isSaving ? t('common.saving') : t('common.save') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isEditDialogOpen">
      <DialogContent class="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle>{{ t('accounts.editDialog.title', { name: editName }) }}</DialogTitle>
          <DialogDescription>{{ t('accounts.editDialog.description') }}</DialogDescription>
        </DialogHeader>
        <div class="space-y-4">
          <div class="grid gap-2">
            <Label>{{ t('accounts.createDialog.jsonContent') }}</Label>
            <Textarea v-model="editContent" class="min-h-[200px]" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isEditDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button :disabled="isSaving" @click="handleUpdateAccount">
            {{ isSaving ? t('common.saving') : t('common.save') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{{ t('accounts.deleteDialog.title') }}</DialogTitle>
          <DialogDescription>{{ t('accounts.deleteDialog.description', { name: deleteName }) }}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" :disabled="isSaving" @click="handleDeleteAccount">
            {{ isSaving ? t('accounts.deleteDialog.deleting') : t('accounts.list.delete') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
