
<script setup lang="ts">
import { onMounted, watch } from 'vue';
import ThemeToggle from './ThemeToggle.vue';
import { themeStore } from '@/stores/themeStore';

defineProps<{
  title: string;
  subtitle?: string;
}>();

onMounted(() => {
  themeStore.initTheme();
});

// Watch para forzar la actualización de la clase dark
watch(() => themeStore.isDark, () => {
  themeStore.applyTheme();
});
</script>

<template>
  <div class="flex justify-center items-center min-h-screen p-4 relative overflow-hidden transition-colors duration-300">
    <!-- Theme Toggle - Top Right -->
    <div class="absolute top-6 right-6 z-20">
      <ThemeToggle />
    </div>

    <!-- Decorative background elements -->
  <div class="absolute top-0 left-0 w-96 h-96 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob bg-blue-200 dark:bg-blue-900"></div>
  <div class="absolute top-0 right-0 w-96 h-96 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000 bg-purple-100 dark:bg-purple-900"></div>
  <div class="absolute bottom-0 left-1/2 w-96 h-96 rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-blob animation-delay-4000 bg-pink-100 dark:bg-pink-900"></div>

  <div
    class="py-12 px-12 rounded-2xl shadow-2xl border w-full max-w-[480px] text-center relative z-10 transition-colors duration-300 bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700"
    :style="themeStore.isDark ? '' : 'background-color: #fff;'"
  >
      <div class="mb-10">
        <div class="flex justify-center mb-6">
          <img src="@/assets/Logo Embalse IoT.png" alt="Embalses IoT Logo" class="h-20 w-auto object-contain drop-shadow-md">
        </div>
        <h2 class="my-3 text-2xl font-bold tracking-tight transition-colors text-gray-800 dark:text-gray-100">{{ title }}</h2>
        <p v-if="subtitle" class="m-0 text-base transition-colors text-gray-600 dark:text-gray-400">{{ subtitle }}</p>
      </div>
      <slot />
    </div>
  </div>
</template>
