<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { authStore } from '@/auth/store';
import { alertStore } from '@/stores/alertStore';
import { APP_NAME } from '@/utils/constants';

defineOptions({
  name: 'AppSidebar'
});

defineProps<{
  isCollapsed: boolean
}>();
const emit = defineEmits(['toggle-sidebar']);
</script>

<template>
  <aside
    class="bg-gray-800 text-gray-100 flex flex-col justify-between shadow-lg transition-all duration-300 flex-shrink-0"
    :class="isCollapsed ? 'w-[88px]' : 'w-sidebar-expanded'"
  >
    <!-- Sidebar Content -->
    <div class="flex flex-col h-full">
      <!-- Header -->
      <div
        class="flex items-center gap-3 h-header flex-shrink-0 overflow-hidden border-b border-gray-700"
        :class="isCollapsed ? 'justify-center px-0' : 'px-7'"
      >
        <i class="pi pi-shield text-3xl flex-shrink-0"></i>
        <h2 v-if="!isCollapsed" class="text-xl font-semibold whitespace-nowrap">
          {{ APP_NAME }}
        </h2>
      </div>

      <!-- Navigation -->
      <nav class="p-4">
        <!-- Dashboard Link -->
        <RouterLink
          to="/"
          class="flex items-center px-4 py-3.5 text-gray-400 no-underline rounded-md mb-2 transition-all duration-200 whitespace-nowrap hover:bg-gray-700 hover:text-white"
          :class="isCollapsed ? 'justify-center' : ''"
          active-class="!bg-primary-500 !text-white font-medium"
        >
          <i class="pi pi-th-large text-2xl w-6 text-center flex-shrink-0" :class="isCollapsed ? '' : 'mr-6'"></i>
          <span v-if="!isCollapsed">Dashboard</span>
        </RouterLink>

        <!-- Alerts Link -->
        <RouterLink
          to="/alerts"
          class="flex items-center px-4 py-3.5 text-gray-400 no-underline rounded-md mb-2 transition-all duration-200 whitespace-nowrap hover:bg-gray-700 hover:text-white relative"
          :class="[
            isCollapsed ? 'justify-center' : '',
            alertStore.summary.total > 0 && !alertStore.summary.critical ? 'bg-warning-500/10 border-l-4 border-warning-500' : '',
            alertStore.summary.critical > 0 ? 'bg-danger-500/10 border-l-4 border-danger-500' : ''
          ]"
          active-class="!bg-primary-500 !text-white font-medium"
        >
          <div class="relative flex items-center">
            <!-- Icon based on alert status -->
            <i
              v-if="alertStore.summary.critical > 0"
              class="pi pi-exclamation-triangle text-2xl w-6 text-center flex-shrink-0 text-danger-500 animate-pulse"
              :class="isCollapsed ? '' : 'mr-6'"
            ></i>
            <i
              v-else-if="alertStore.summary.total > 0"
              class="pi pi-exclamation-circle text-2xl w-6 text-center flex-shrink-0 text-warning-500"
              :class="isCollapsed ? '' : 'mr-6'"
            ></i>
            <i
              v-else
              class="pi pi-bell text-2xl w-6 text-center flex-shrink-0"
              :class="isCollapsed ? '' : 'mr-6'"
            ></i>

            <!-- Alert indicator (dot when expanded) -->
            <span
              v-if="alertStore.summary.total > 0 && !isCollapsed"
              class="absolute -top-0.5 -right-0.5 w-2 h-2 bg-danger-500 rounded-full animate-pulse"
            ></span>

            <!-- Alert badge (number when collapsed) -->
            <span
              v-if="alertStore.summary.total > 0 && isCollapsed"
              class="absolute -top-2 -right-2 bg-danger-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center font-bold border-2 border-gray-800"
            >
              {{ alertStore.summary.total }}
            </span>
          </div>

          <span v-if="!isCollapsed" class="flex items-center">
            Alertas
            <span
              class="font-bold ml-2"
              :class="{
                'text-danger-500': alertStore.summary.critical > 0,
                'text-warning-500': alertStore.summary.warning > 0 && alertStore.summary.critical === 0,
                'text-gray-400': alertStore.summary.total === 0
              }"
            >
              ({{ alertStore.summary.total }})
            </span>
          </span>
        </RouterLink>

        <!-- Users Link (Admin only) -->
        <RouterLink
          v-if="authStore.user?.role === 'admin'"
          to="/users"
          class="flex items-center px-4 py-3.5 text-gray-400 no-underline rounded-md mb-2 transition-all duration-200 whitespace-nowrap hover:bg-gray-700 hover:text-white"
          :class="isCollapsed ? 'justify-center' : ''"
          active-class="!bg-primary-500 !text-white font-medium"
        >
          <i class="pi pi-users text-2xl w-6 text-center flex-shrink-0" :class="isCollapsed ? '' : 'mr-6'"></i>
          <span v-if="!isCollapsed">Usuarios</span>
        </RouterLink>
      </nav>
    </div>

    <!-- Footer Toggle Button -->
    <div class="p-4 border-t border-gray-700">
      <button
        @click="emit('toggle-sidebar')"
        title="Colapsar/Expandir Menú"
        class="w-full bg-gray-700 border-none text-gray-400 text-2xl cursor-pointer p-2 rounded-md flex justify-center items-center transition-all duration-300 hover:bg-gray-600 hover:text-white"
      >
        <i class="pi" :class="isCollapsed ? 'pi-align-right' : 'pi-align-left'"></i>
      </button>
    </div>
  </aside>
</template>

<!-- Todos los estilos ahora son manejados por Tailwind CSS -->
