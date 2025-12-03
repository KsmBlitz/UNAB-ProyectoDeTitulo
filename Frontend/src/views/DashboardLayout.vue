<script setup lang="ts">
import { ref } from 'vue';
import { RouterView } from 'vue-router';
import Sidebar from '@/components/Sidebar.vue';
import TheHeader from '@/components/TheHeader.vue';
import RouteLoader from '@/components/RouteLoader.vue';
import { useInactivityLogout } from '@/composables/useInactivityLogout';

defineOptions({
  name: 'DashboardLayout'
});

const isSidebarCollapsed = ref(false);
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

// Sistema de cierre de sesión por inactividad
const { 
  showWarningModal, 
  secondsRemaining, 
  continueSession, 
  logoutNow 
} = useInactivityLogout();

// El polling de alertas se manejará desde AlertsManagementView cuando sea necesario
</script>

<template>
  <div class="flex h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100">
    <Sidebar :is-collapsed="isSidebarCollapsed" @toggle-sidebar="toggleSidebar" />

  <div class="flex-grow flex flex-col h-screen overflow-hidden max-w-full">
      <TheHeader />

  <main class="flex-grow overflow-y-auto bg-gradient-to-br from-white via-blue-50 to-blue-100 px-0 relative">
        <!-- Barra de carga en la parte superior del contenido -->
        <RouteLoader />
        
        <RouterView />
      </main>
    </div>
    
    <!-- Modal de advertencia de inactividad -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showWarningModal"
          class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999] p-4"
        >
          <div 
            class="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-bounce-in border-2 border-orange-200"
          >
            <!-- Header con icono animado -->
            <div class="bg-gradient-to-r from-orange-500 to-amber-500 px-6 py-5">
              <div class="flex items-center gap-4">
                <div class="bg-white/20 rounded-full p-3 animate-pulse">
                  <i class="pi pi-clock text-white text-3xl"></i>
                </div>
                <div>
                  <h3 class="text-xl font-bold text-white">
                    Sesión por expirar
                  </h3>
                  <p class="text-orange-100 text-sm">
                    Detectamos inactividad en tu cuenta
                  </p>
                </div>
              </div>
            </div>
            
            <!-- Body -->
            <div class="p-6 text-center">
              <div class="mb-6">
                <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-orange-100 mb-4">
                  <span class="text-3xl font-bold text-orange-600">{{ secondsRemaining }}</span>
                </div>
                <p class="text-gray-600">
                  Tu sesión se cerrará automáticamente en <strong class="text-orange-600">{{ secondsRemaining }} segundos</strong> por inactividad.
                </p>
              </div>
              
              <p class="text-sm text-gray-500 mb-6">
                ¿Deseas continuar trabajando o cerrar la sesión ahora?
              </p>
              
              <!-- Botones -->
              <div class="flex gap-3">
                <button
                  @click="logoutNow"
                  class="flex-1 px-4 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-100 transition-all font-semibold flex items-center justify-center gap-2"
                >
                  <i class="pi pi-sign-out"></i>
                  Cerrar sesión
                </button>
                <button
                  @click="continueSession"
                  class="flex-1 px-4 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all font-semibold shadow-lg flex items-center justify-center gap-2"
                >
                  <i class="pi pi-check"></i>
                  Continuar
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.animate-bounce-in {
  animation: bounce-in 0.4s ease-out;
}
</style>
