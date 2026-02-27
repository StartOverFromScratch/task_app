<script setup lang="ts">
useHead({ htmlAttrs: { lang: 'ja' } })
useSeoMeta({ title: 'タスク管理' })
</script>

<template>
  <UApp>
    <UHeader>
      <template #left>
        <NuxtLink
          to="/"
          class="font-bold text-lg text-primary"
        >タスク管理</NuxtLink>
      </template>
      <template #right>
        <UButton
          to="/"
          variant="ghost"
          color="neutral"
        >
          タスク
        </UButton>
        <UButton
          to="/carryover"
          variant="ghost"
          color="neutral"
        >
          繰り越し
        </UButton>
        <UButton
          to="/stale"
          variant="ghost"
          color="neutral"
        >
          放置
        </UButton>
        <UButton
          to="/capture"
          variant="ghost"
          color="neutral"
        >
          Capture
        </UButton>
        <UColorModeButton />
      </template>
    </UHeader>
    <UMain>
      <UContainer class="py-6">
        <NuxtPage />
      </UContainer>
    </UMain>
  </UApp>
</template>
