<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import type { RotationSettings } from '@/api/settings'

defineProps<{
  settings: RotationSettings
  isReady: boolean
  isSaving: boolean
}>()
const { t } = useI18n()

const emit = defineEmits<{
  (e: 'save'): void
}>()
</script>

<template>
  <Card class="app-surface overflow-hidden border-none">
    <CardHeader class="settings-card-header">
      <CardTitle>{{ t('rotation.title') }}</CardTitle>
      <CardDescription>{{ t('rotation.description') }}</CardDescription>
    </CardHeader>
    <CardContent v-if="isReady" class="settings-card-content grid gap-6 lg:grid-cols-2">
      <section class="settings-subsection">
        <div class="mb-6 flex items-start justify-between gap-4">
          <div class="min-w-0">
            <h3 class="font-semibold text-slate-900">{{ t('rotation.account.title') }}</h3>
            <p class="mt-1 text-sm leading-5 text-slate-500">{{ t('rotation.account.description') }}</p>
          </div>
          <Switch class="shrink-0" v-model:checked="settings.ACCOUNT_ROTATION_ENABLED" />
        </div>

        <div class="grid gap-5">
          <div class="settings-field">
            <Label>{{ t('rotation.account.stateDir') }}</Label>
            <Input v-model="settings.ACCOUNT_STATE_DIR" class="settings-input" placeholder="state" />
          </div>
          <div class="settings-field">
            <Label>{{ t('rotation.mode') }}</Label>
            <Select v-model="settings.ACCOUNT_ROTATION_MODE">
              <SelectTrigger class="settings-select-trigger">
                <SelectValue :placeholder="t('rotation.modePlaceholder')" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="per_task">{{ t('rotation.perTask') }}</SelectItem>
                <SelectItem value="on_failure">{{ t('rotation.onFailure') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-5 sm:grid-cols-2">
            <div class="settings-field">
              <Label>{{ t('rotation.retryLimit') }}</Label>
              <Input v-model.number="settings.ACCOUNT_ROTATION_RETRY_LIMIT" class="settings-input" type="number" min="1" />
            </div>
            <div class="settings-field">
              <Label>{{ t('rotation.blacklistTtl') }}</Label>
              <Input v-model.number="settings.ACCOUNT_BLACKLIST_TTL" class="settings-input" type="number" min="0" />
            </div>
          </div>
        </div>
      </section>

      <section class="settings-subsection">
        <div class="mb-6 flex items-start justify-between gap-4">
          <div class="min-w-0">
            <h3 class="font-semibold text-slate-900">{{ t('rotation.proxy.title') }}</h3>
            <p class="mt-1 text-sm leading-5 text-slate-500">{{ t('rotation.proxy.description') }}</p>
          </div>
          <Switch class="shrink-0" v-model:checked="settings.PROXY_ROTATION_ENABLED" />
        </div>

        <div class="grid gap-5">
          <div class="settings-field">
            <Label>{{ t('rotation.mode') }}</Label>
            <Select v-model="settings.PROXY_ROTATION_MODE">
              <SelectTrigger class="settings-select-trigger">
                <SelectValue :placeholder="t('rotation.modePlaceholder')" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="per_task">{{ t('rotation.perTask') }}</SelectItem>
                <SelectItem value="on_failure">{{ t('rotation.onFailure') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="settings-field">
            <Label>{{ t('rotation.proxy.pool') }}</Label>
            <Textarea
              v-model="settings.PROXY_POOL"
              class="min-h-[140px]"
              placeholder="http://127.0.0.1:7890,socks5://127.0.0.1:1080"
            />
          </div>
          <div class="grid gap-5 sm:grid-cols-2">
            <div class="settings-field">
              <Label>{{ t('rotation.retryLimit') }}</Label>
              <Input v-model.number="settings.PROXY_ROTATION_RETRY_LIMIT" class="settings-input" type="number" min="1" />
            </div>
            <div class="settings-field">
              <Label>{{ t('rotation.blacklistTtl') }}</Label>
              <Input v-model.number="settings.PROXY_BLACKLIST_TTL" class="settings-input" type="number" min="0" />
            </div>
          </div>
        </div>
      </section>
    </CardContent>
    <CardContent v-else class="settings-card-content py-8 text-sm text-slate-500">
      {{ t('rotation.loading') }}
    </CardContent>
    <CardFooter v-if="isReady" class="settings-card-footer flex justify-end">
      <Button @click="emit('save')" :disabled="isSaving">{{ t('rotation.save') }}</Button>
    </CardFooter>
  </Card>
</template>
