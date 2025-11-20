<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';

defineOptions({
  name: 'RouteLoader'
});

const router = useRouter();
const isLoading = ref(false);

// Mostrar loader cuando cambia la ruta
router.beforeEach(() => {
  isLoading.value = true;
  return true;
});

router.afterEach(() => {
  // Pequeño delay para que se vea el loader en conexiones rápidas
  setTimeout(() => {
    isLoading.value = false;
  }, 100);
});
</script>

<template>
  <Transition name="fade">
    <div
      v-if="isLoading"
      class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent bg-[length:200%_100%] animate-shimmer z-50 shadow-lg shadow-blue-500/50"
      style="height: 3px;"
    ></div>
  </Transition>
</template>

<style scoped>
@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.animate-shimmer {
  animation: shimmer 1.5s ease-in-out infinite;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
