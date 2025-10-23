<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { onMounted, onUnmounted } from 'vue';
import { authStore } from '@/auth/store';
import { alertStore } from '@/stores/alertStore';
import { useClickOutside } from '@/composables/useClickOutside';

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
function handleLogout() {
  console.log('Cerrando sesión...');
  localStorage.removeItem('userToken');
  authStore.user = null;
  router.push('/login');
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
  <header class="flex justify-between items-center px-6 py-3 bg-white border-b border-gray-200 flex-shrink-0">
    <!-- Left Section -->
    <div class="flex items-center gap-6">
      <div class="flex items-center gap-2 border border-gray-300 px-4 py-2 rounded-md cursor-pointer hover:bg-gray-50 transition-colors">
        <i class="pi pi-map-marker text-gray-600"></i>
        <span class="text-gray-700">Ubicación</span>
        <i class="pi pi-chevron-down text-gray-500 text-sm"></i>
      </div>
    </div>

    <!-- Right Section -->
    <div class="flex items-center gap-6">
      <!-- Alerts Counter -->
      <div
        @click="navigateToAlerts"
        class="relative cursor-pointer p-2 rounded-md transition-all hover:bg-gray-100"
      >
        <i
          class="pi pi-exclamation-triangle text-2xl transition-colors"
          :class="hasCriticalAlerts ? 'text-danger-500' : 'text-gray-600'"
        ></i>
        <span
          v-if="hasAlerts"
          class="absolute -top-1 -right-1 rounded-full w-5 h-5 text-xs flex justify-center items-center font-bold"
          :class="hasCriticalAlerts ? 'bg-danger-500 text-white' : 'bg-warning-500 text-gray-900'"
        >
          {{ alertSummary.total }}
        </span>
      </div>

      <!-- User Profile -->
      <div
        ref="userProfileRef"
        @click="toggleUserMenu"
        class="relative flex items-center gap-3 cursor-pointer p-2 rounded-lg transition-colors hover:bg-gray-100"
      >
        <!-- Avatar -->
        <div class="w-10 h-10 rounded-full bg-gray-200 flex justify-center items-center">
          <i class="pi pi-user text-xl text-gray-600"></i>
        </div>

        <!-- User Info -->
        <div class="flex flex-col items-start">
          <span class="font-bold text-sm text-gray-800">{{ authStore.user?.full_name || 'Usuario' }}</span>
          <span class="text-xs text-gray-600">{{ userRoleFormatted }}</span>
        </div>

        <!-- User Menu Dropdown -->
        <div
          v-if="isMenuOpen"
          class="absolute top-full right-0 mt-2 w-72 bg-gray-800 text-gray-100 rounded-lg shadow-modal z-[1000] overflow-hidden"
        >
          <!-- Menu Header -->
          <div class="p-6 text-center border-b border-gray-700">
            <span class="block font-semibold text-white">{{ authStore.user?.full_name || 'Usuario' }}</span>
            <span class="block text-sm text-gray-400 mt-1">{{ authStore.user?.email || 'Sin email' }}</span>
          </div>

          <!-- Menu Items -->
          <ul class="list-none p-2 m-0">
            <li class="flex items-center gap-4 px-4 py-3 rounded-md transition-colors hover:bg-gray-700 cursor-pointer">
              <i class="pi pi-user-edit text-xl w-6 text-center"></i>
              <span>Editar Perfil</span>
            </li>
            <li class="flex items-center gap-4 px-4 py-3 rounded-md transition-colors hover:bg-gray-700 cursor-pointer">
              <i class="pi pi-cog text-xl w-6 text-center"></i>
              <span>Configuración</span>
            </li>
            <li
              @click="handleLogout"
              class="flex items-center gap-4 px-4 py-3 rounded-md transition-colors hover:bg-danger-600 cursor-pointer text-danger-400 hover:text-white"
            >
              <i class="pi pi-sign-out text-xl w-6 text-center"></i>
              <span>Cerrar Sesión</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>

<!-- Todos los estilos ahora son manejados por Tailwind CSS -->
