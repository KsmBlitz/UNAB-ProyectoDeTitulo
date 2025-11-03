<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { onMounted, onUnmounted } from 'vue';
import { authStore } from '@/auth/store';
import { alertStore } from '@/stores/alertStore';
import { useClickOutside } from '@/composables/useClickOutside';
import { API_BASE_URL } from '@/config/api';

defineOptions({
  name: 'TheHeader'
});

const router = useRouter();

// Estado del menú de usuario
const isMenuOpen = ref(false);
const userProfileRef = ref<HTMLDivElement | null>(null);

// Usar composable para cerrar menú al hacer clic fuera
useClickOutside(userProfileRef, () => {
  isMenuOpen.value = false;
});

// Toggle del menú
function toggleUserMenu() {
  isMenuOpen.value = !isMenuOpen.value;
}

// Cerrar sesión
async function handleLogout() {
  console.log('Cerrando sesión...');
  
  try {
    const token = localStorage.getItem('userToken');
    
    // Llamar al endpoint de logout para registrar en auditoría
    if (token) {
      await fetch(`${API_BASE_URL}/api/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
    }
  } catch (error) {
    console.error('Error al registrar logout:', error);
    // Continuar con el logout incluso si falla el registro
  } finally {
    // Limpiar localStorage y redirigir
    localStorage.removeItem('userToken');
    authStore.user = null;
    router.push('/login');
  }
}

// Navegar a alertas
function navigateToAlerts() {
  router.push('/alerts');
}

// Datos de alertas
const alertSummary = computed(() => alertStore.summary);
const hasAlerts = computed(() => alertSummary.value.total > 0);
const hasCriticalAlerts = computed(() => alertSummary.value.critical > 0);

// Rol del usuario formateado
const userRoleFormatted = computed(() => {
  switch (authStore.user?.role) {
    case 'admin': return 'Administrador';
    case 'operario': return 'Operario';
    default: return 'Usuario';
  }
});

onMounted(() => {
  alertStore.startPolling();
});

onUnmounted(() => {
  alertStore.stopPolling();
});
</script>

<template>
  <header class="flex justify-between items-center px-8 py-4 bg-white border-b border-gray-200 flex-shrink-0 shadow-sm">
    <!-- Left Section -->
    <div class="flex items-center gap-6">
      <div class="flex items-center gap-3 border border-gray-300 px-5 py-2.5 rounded-lg cursor-pointer hover:bg-gray-50 hover:border-gray-400 transition-all group">
        <i class="pi pi-map-marker text-gray-600 group-hover:text-blue-600 transition-colors"></i>
        <span class="text-sm font-medium text-gray-700 group-hover:text-gray-900">Ubicación</span>
        <i class="pi pi-chevron-down text-gray-400 text-xs group-hover:text-gray-600 transition-colors"></i>
      </div>
    </div>

    <!-- Right Section -->
    <div class="flex items-center gap-4">
      <!-- Alerts Counter -->
      <div
        @click="navigateToAlerts"
        class="relative cursor-pointer p-3 rounded-lg transition-all hover:bg-gray-100 group"
      >
        <i
          class="pi pi-bell text-xl transition-colors"
          :class="hasCriticalAlerts ? 'text-red-600' : hasAlerts ? 'text-orange-600' : 'text-gray-500'"
        ></i>
        <span
          v-if="hasAlerts"
          class="absolute -top-0.5 -right-0.5 rounded-full w-5 h-5 text-[10px] flex justify-center items-center font-bold shadow-lg border-2 border-white"
          :class="hasCriticalAlerts ? 'bg-red-600 text-white' : 'bg-orange-500 text-white'"
        >
          {{ alertSummary.total }}
        </span>
      </div>

      <!-- User Profile -->
      <div
        ref="userProfileRef"
        @click="toggleUserMenu"
        class="relative flex items-center gap-3 cursor-pointer px-4 py-2 rounded-lg transition-all hover:bg-gray-50 border border-transparent hover:border-gray-300"
      >
        <!-- Avatar -->
        <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex justify-center items-center shadow-md">
          <i class="pi pi-user text-base text-white"></i>
        </div>

        <!-- User Info -->
        <div class="flex flex-col items-start">
          <span class="font-semibold text-sm text-gray-800">{{ authStore.user?.full_name || 'Usuario' }}</span>
          <span class="text-xs text-gray-500">{{ userRoleFormatted }}</span>
        </div>

        <i class="pi pi-chevron-down text-xs text-gray-400"></i>

        <!-- User Menu Dropdown -->
        <div
          v-if="isMenuOpen"
          class="absolute top-full right-0 mt-3 w-64 bg-white rounded-xl shadow-2xl border border-gray-200 z-[1000] overflow-hidden"
        >
          <!-- Menu Header -->
          <div class="p-5 bg-gradient-to-br from-slate-50 to-gray-100 border-b border-gray-200">
            <span class="block font-semibold text-gray-900 text-sm">{{ authStore.user?.full_name || 'Usuario' }}</span>
            <span class="block text-xs text-gray-600 mt-1">{{ authStore.user?.email || 'Sin email' }}</span>
          </div>

          <!-- Menu Items -->
          <ul class="list-none p-2 m-0">
            <li class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all hover:bg-gray-100 cursor-pointer text-gray-700 hover:text-gray-900">
              <i class="pi pi-user-edit text-base w-5 text-center text-gray-600"></i>
              <span class="text-sm font-medium">Editar Perfil</span>
            </li>
            <li class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all hover:bg-gray-100 cursor-pointer text-gray-700 hover:text-gray-900">
              <i class="pi pi-cog text-base w-5 text-center text-gray-600"></i>
              <span class="text-sm font-medium">Configuración</span>
            </li>
            <li class="border-t border-gray-200 mt-2 pt-2"></li>
            <li
              @click="handleLogout"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all hover:bg-red-50 cursor-pointer text-red-600 hover:text-red-700"
            >
              <i class="pi pi-sign-out text-base w-5 text-center"></i>
              <span class="text-sm font-medium">Cerrar Sesión</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>

