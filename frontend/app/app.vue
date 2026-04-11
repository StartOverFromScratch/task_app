<script setup lang="ts">
useHead({ htmlAttrs: { lang: 'ja' } })
useSeoMeta({ title: 'Tapp' })
</script>

<template>
  <UApp>
    <UHeader>
      <template #left>
        <NuxtLink
          to="/"
          class="font-bold text-lg text-primary"
        >Tapp</NuxtLink>
      </template>
      <template #right />
    </UHeader>
    <UMain>
      <UContainer class="py-6">
        <NuxtPage />
      </UContainer>
    </UMain>
  </UApp>
</template>
