<script setup lang="ts">
import type { NavItem } from '~/composables/useNavItems'

const { modelValue, staleCount = 0, carryoverCount = 0 } = defineProps<{
  modelValue: string
  staleCount?: number
  carryoverCount?: number
}>()

const emit = defineEmits<{
  'update:modelValue': [key: string]
  'navigate': [item: NavItem]
}>()

const { NAV_ITEMS } = useNavItems()

function handleClick(item: NavItem) {
  if (!item.to) {
    emit('update:modelValue', item.key)
  }
  emit('navigate', item)
}

function getBadgeCount(key: string): number | null {
  if (key === 'stale') return staleCount > 0 ? staleCount : null
  if (key === 'carryover') return carryoverCount > 0 ? carryoverCount : null
  return null
}
</script>

<template>
  <nav class="flex flex-col gap-1 p-2">
    <template
      v-for="item in NAV_ITEMS"
      :key="item.key"
    >
      <UDivider
        v-if="item.key === 'stale'"
        class="my-2"
      />
      <component
        :is="item.to ? 'NuxtLink' : 'button'"
        :to="item.to"
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-xl font-medium transition-colors w-full text-left"
        :class="[
          !item.to && modelValue === item.key
            ? 'bg-primary text-white'
            : 'hover:bg-elevated text-default'
        ]"
        @click="handleClick(item)"
      >
        <UIcon
          :name="item.icon"
          class="w-4 h-4 shrink-0"
        />
        <span class="flex-1">{{ item.label }}</span>
        <UBadge
          v-if="getBadgeCount(item.key) !== null"
          :label="String(getBadgeCount(item.key))"
          color="neutral"
          variant="subtle"
          size="sm"
        />
      </component>
    </template>
  </nav>
</template>
