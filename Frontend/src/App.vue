<script setup lang="ts">
import { RouterView } from 'vue-router'
import NotificationToast from '@/components/NotificationToast.vue'
import PWAUpdatePrompt from '@/components/PWAUpdatePrompt.vue'
</script>

<template>
  <div id="app">
    <RouterView />
    <NotificationToast />
    <PWAUpdatePrompt />
  </div>
</template>

<!-- Global styles now managed by Tailwind CSS in assets/styles.css -->
