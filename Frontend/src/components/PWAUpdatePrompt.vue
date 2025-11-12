// Frontend/src/components/PWAUpdatePrompt.vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRegisterSW } from 'virtual:pwa-register/vue'

defineOptions({
  name: 'PWAUpdatePrompt'
})

const {
  needRefresh,
  updateServiceWorker,
} = useRegisterSW({
  onRegistered(r: any) {
    console.log('[PWA] Service Worker registered:', r)
    
    // Check for updates every hour
    r && setInterval(() => {
      r.update()
    }, 60 * 60 * 1000)
  },
  onRegisterError(error: any) {
    console.error('[PWA] Service Worker registration error:', error)
  },
})

const showUpdatePrompt = ref(false)

onMounted(() => {
  if (needRefresh.value) {
    showUpdatePrompt.value = true
  }
})

const updateApp = async () => {
  await updateServiceWorker()
  showUpdatePrompt.value = false
  window.location.reload()
}

const dismissUpdate = () => {
  showUpdatePrompt.value = false
}
</script>

<template>
  <!-- Toast de actualización disponible -->
  <Transition name="slide-up">
    <div
      v-if="showUpdatePrompt && needRefresh"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[9999] max-w-md w-full mx-4 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
    >
      <div class="p-6">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
            <i class="pi pi-sync text-2xl text-blue-600 dark:text-blue-400"></i>
          </div>
          
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Nueva versión disponible
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">
              Hay una nueva versión de la aplicación. Actualiza para obtener las últimas mejoras y correcciones.
            </p>
            
            <div class="flex gap-3">
              <button
                @click="updateApp"
                class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                <i class="pi pi-refresh mr-2"></i>
                Actualizar ahora
              </button>
              
              <button
                @click="dismissUpdate"
                class="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
              >
                Más tarde
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease-out;
}

.slide-up-enter-from {
  transform: translate(-50%, 100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translate(-50%, 100%);
  opacity: 0;
}
</style>
