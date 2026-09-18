<script setup lang="ts">
withDefaults(defineProps<{
  size?: number | string
  label?: string
}>(), {
  size: 40,
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :role="label ? 'img' : undefined"
    :aria-label="label"
    :aria-hidden="label ? undefined : 'true'"
  >
    <title v-if="label">{{ label }}</title>
    <rect x="2" y="2" width="60" height="60" rx="18" fill="#0B1F3A" />
    <circle cx="32" cy="32" r="21" stroke="#164B73" stroke-width="2" />
    <circle cx="32" cy="32" r="15" stroke="#38D5FF" stroke-width="2" stroke-dasharray="2 5" opacity="0.72" />
    <path d="M11 32H53M32 11V53" stroke="#38D5FF" stroke-width="1.5" opacity="0.24" />
    <path d="M18 34C22 27 29 23 36 25C41 26 45 30 48 34C45 38 41 42 36 43C29 45 22 41 18 34Z" fill="#E9FBFF" />
    <path d="M18 34L11 27V41L18 34Z" fill="#7CEBFF" />
    <circle cx="39" cy="31" r="2" fill="#0B1F3A" />
    <path d="M47 16L39 31L53 24" stroke="#B6F36A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
    <circle cx="47" cy="16" r="3" fill="#B6F36A" />
  </svg>
</template>
