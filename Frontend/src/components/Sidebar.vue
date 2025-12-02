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
    class="bg-white text-gray-800 flex flex-col justify-between shadow-xl transition-all duration-300 flex-shrink-0 border-r border-gray-200 m-3 mr-0 rounded-l-2xl"
    :class="isCollapsed ? 'w-[80px]' : 'w-sidebar-expanded'"
  >
    <!-- Sidebar Content -->
    <div class="flex flex-col h-full">
      <!-- Header -->
      <div
        class="flex items-center gap-4 h-header flex-shrink-0 overflow-hidden border-b border-gray-200 bg-white mt-0 rounded-tl-2xl"
        :class="isCollapsed ? 'justify-center px-0' : 'px-6'"
      >
        <div class="w-10 h-10 flex items-center justify-center flex-shrink-0">
          <img src="@/assets/Logo Embalse IoT.png" alt="Logo" class="w-10 h-10 object-contain">
        </div>
        <h2 v-if="!isCollapsed" class="text-lg font-bold whitespace-nowrap tracking-wide text-gray-800">
          {{ APP_NAME }}
        </h2>
      </div>

      <!-- Navigation -->
  <nav class="p-3 mt-0">
        <!-- Dashboard Link -->
        <RouterLink
          to="/"
          class="flex items-center px-4 py-3 text-gray-700 no-underline rounded-lg mb-1 transition-all duration-200 whitespace-nowrap hover:bg-blue-100 hover:text-blue-700 group"
          :class="isCollapsed ? 'justify-center' : ''"
          exact-active-class="!bg-gradient-to-r !from-blue-600 !to-blue-500 !text-white !shadow-lg !shadow-blue-500/30"
        >
          <i class="pi pi-th-large text-lg w-5 text-center flex-shrink-0 group-hover:scale-110 transition-transform" :class="isCollapsed ? '' : 'mr-4'"></i>
          <span v-if="!isCollapsed" class="font-medium text-sm">Dashboard</span>
        </RouterLink>

        <!-- Alerts Link -->
        <RouterLink
          to="/alerts"
          class="flex items-center px-4 py-3 text-gray-700 no-underline rounded-lg mb-1 transition-all duration-200 whitespace-nowrap hover:bg-blue-100 hover:text-blue-700 relative group"
          :class="[
            isCollapsed ? 'justify-center' : '',
            alertStore.summary.total > 0 && !alertStore.summary.critical ? 'bg-orange-100 border-l-2 border-orange-500' : '',
            alertStore.summary.critical > 0 ? 'bg-red-100 border-l-2 border-red-500 animate-pulse' : ''
          ]"
          active-class="!bg-gradient-to-r !from-blue-600 !to-blue-500 !text-white !shadow-lg !shadow-blue-500/30"
        >
          <div class="relative flex items-center">
            <!-- Icon based on alert status -->
            <i
              v-if="alertStore.summary.critical > 0"
              class="pi pi-exclamation-triangle text-lg w-5 text-center flex-shrink-0 text-red-400 group-hover:scale-110 transition-transform"
              :class="isCollapsed ? '' : 'mr-4'"
            ></i>
            <i
              v-else-if="alertStore.summary.total > 0"
              class="pi pi-exclamation-circle text-lg w-5 text-center flex-shrink-0 text-orange-400 group-hover:scale-110 transition-transform"
              :class="isCollapsed ? '' : 'mr-4'"
            ></i>
            <i
              v-else
              class="pi pi-bell text-lg w-5 text-center flex-shrink-0 group-hover:scale-110 transition-transform"
              :class="isCollapsed ? '' : 'mr-4'"
            ></i>

            <!-- Alert badge (number when collapsed) -->
            <span
              v-if="alertStore.summary.total > 0 && isCollapsed"
              class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-4 h-4 text-[10px] flex items-center justify-center font-bold border border-slate-900 shadow-lg"
            >
              {{ alertStore.summary.total }}
            </span>
          </div>

          <span v-if="!isCollapsed" class="flex items-center font-medium text-sm">
            Alertas
            <span
              v-if="alertStore.summary.total > 0"
              class="ml-auto px-2 py-0.5 rounded-full text-xs font-bold"
              :class="{
                'bg-red-500/20 text-red-300': alertStore.summary.critical > 0,
                'bg-orange-500/20 text-orange-300': alertStore.summary.warning > 0 && alertStore.summary.critical === 0,
              }"
            >
              {{ alertStore.summary.total }}
            </span>
          </span>
        </RouterLink>

        <!-- Analytics Link -->
        <RouterLink
          to="/analytics"
          class="flex items-center px-4 py-3 text-gray-700 no-underline rounded-lg mb-1 transition-all duration-200 whitespace-nowrap hover:bg-blue-100 hover:text-blue-700 group"
          :class="isCollapsed ? 'justify-center' : ''"
          active-class="!bg-gradient-to-r !from-blue-600 !to-blue-500 !text-white !shadow-lg !shadow-blue-500/30"
        >
          <i class="pi pi-chart-line text-lg w-5 text-center flex-shrink-0 group-hover:scale-110 transition-transform" :class="isCollapsed ? '' : 'mr-4'"></i>
          <span v-if="!isCollapsed" class="font-medium text-sm">Analítica</span>
        </RouterLink>

        <!-- Users Link (Admin only) -->
        <RouterLink
          v-if="authStore.user?.role === 'admin'"
          to="/users"
          class="flex items-center px-4 py-3 text-gray-700 no-underline rounded-lg mb-1 transition-all duration-200 whitespace-nowrap hover:bg-blue-100 hover:text-blue-700 group"
          :class="isCollapsed ? 'justify-center' : ''"
          active-class="!bg-gradient-to-r !from-blue-600 !to-blue-500 !text-white !shadow-lg !shadow-blue-500/30"
        >
          <i class="pi pi-users text-lg w-5 text-center flex-shrink-0 group-hover:scale-110 transition-transform" :class="isCollapsed ? '' : 'mr-4'"></i>
          <span v-if="!isCollapsed" class="font-medium text-sm">Usuarios</span>
        </RouterLink>

        <!-- Audit Log Link (Admin only) -->
        <RouterLink
          v-if="authStore.user?.role === 'admin'"
          to="/audit"
          class="flex items-center px-4 py-3 text-gray-700 no-underline rounded-lg mb-1 transition-all duration-200 whitespace-nowrap hover:bg-blue-100 hover:text-blue-700 group"
          :class="isCollapsed ? 'justify-center' : ''"
          active-class="!bg-gradient-to-r !from-blue-600 !to-blue-500 !text-white !shadow-lg !shadow-blue-500/30"
        >
          <i class="pi pi-history text-lg w-5 text-center flex-shrink-0 group-hover:scale-110 transition-transform" :class="isCollapsed ? '' : 'mr-4'"></i>
          <span v-if="!isCollapsed" class="font-medium text-sm">Auditoría</span>
        </RouterLink>
      </nav>
    </div>

    <!-- Footer Toggle Button -->
  <div class="p-3 border-t border-gray-200 bg-white">
      <button
        @click="emit('toggle-sidebar')"
        title="Colapsar/Expandir Menú"
  class="w-full bg-gray-100 border-none text-gray-500 text-lg cursor-pointer p-2.5 rounded-lg flex justify-center items-center transition-all duration-200 hover:bg-blue-100 hover:text-blue-700"
      >
        <i class="pi" :class="isCollapsed ? 'pi-angle-right' : 'pi-angle-left'"></i>
      </button>
    </div>
  </aside>
</template>

