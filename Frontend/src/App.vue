<script setup lang="ts">
import { RouterView } from 'vue-router'
import NotificationToast from '@/components/NotificationToast.vue'
</script>

<template>
  <RouterView />
  <NotificationToast />
</template>

<!-- Global styles now managed by Tailwind CSS in assets/styles.css -->
