<script setup lang="ts">
import { ref } from 'vue';
import { RouterView } from 'vue-router';
import Sidebar from '@/components/Sidebar.vue';
import TheHeader from '@/components/TheHeader.vue';

defineOptions({
  name: 'DashboardLayout'
});

const isSidebarCollapsed = ref(false);
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

// El polling de alertas se manejará desde AlertsManagementView cuando sea necesario
</script>

<template>
  <div class="flex h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-blue-50">
    <Sidebar :is-collapsed="isSidebarCollapsed" @toggle-sidebar="toggleSidebar" />

    <div class="flex-grow flex flex-col h-screen overflow-hidden">
      <TheHeader />

      <main class="flex-grow overflow-y-auto bg-gradient-to-br from-slate-50 via-gray-50 to-blue-50">
        <RouterView />
      </main>
    </div>
  </div>
</template>
