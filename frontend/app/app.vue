<script setup lang="ts">
useHead({ htmlAttrs: { lang: 'ja' } })
useSeoMeta({ title: 'Tapp' })
</script>

<template>
  <UApp>
    <div class="hidden lg:flex items-center h-16 px-6 border-b border-default shrink-0">
      <NuxtLink
        to="/"
        class="font-bold text-lg text-primary"
      >
        Tapp
      </NuxtLink>
    </div>
    <UMain>
      <UContainer class="py-6">
        <NuxtPage />
      </UContainer>
    </UMain>
  </UApp>
</template>
