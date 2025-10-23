<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <div class="flex justify-center items-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 p-4 relative overflow-hidden">
    <!-- Decorative background elements -->
    <div class="absolute top-0 left-0 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
    <div class="absolute top-0 right-0 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
    <div class="absolute bottom-0 left-1/2 w-96 h-96 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>

    <div class="bg-white/80 backdrop-blur-sm py-12 px-12 rounded-2xl shadow-2xl border border-gray-100 w-full max-w-[480px] text-center relative z-10">
      <div class="mb-10">
        <div class="flex justify-center mb-6">
          <img src="@/assets/Logo Embalse IoT.png" alt="Embalses IoT Logo" class="h-24 w-auto object-contain drop-shadow-lg">
        </div>
        <h2 class="my-3 text-gray-800 text-3xl font-bold tracking-tight">{{ title }}</h2>
        <p v-if="subtitle" class="text-gray-600 m-0 text-lg">{{ subtitle }}</p>
      </div>
      <slot />
    </div>
  </div>
</template>
