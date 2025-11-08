<script setup lang="ts">
import { RouterView } from 'vue-router'
import NotificationToast from '@/components/NotificationToast.vue'
</script>

<template>
  <div id="app">
    <RouterView />
    <NotificationToast />
  </div>
</template>

<!-- Global styles now managed by Tailwind CSS in assets/styles.css -->
