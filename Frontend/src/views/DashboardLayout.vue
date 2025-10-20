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
  <div class="dashboard-layout">
    <Sidebar :is-collapsed="isSidebarCollapsed" @toggle-sidebar="toggleSidebar" />

    <div class="main-content-wrapper">
      <TheHeader />

      <main class="dashboard-main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
:root {
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 88px;
  --header-height: 80px; /* Aumentamos la altura para más espacio */
}

.dashboard-layout {
  display: flex;
}

.main-content-wrapper {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden; /* Evita el doble scroll en la ventana */
}

.app-header {
  height: var(--header-height);
  padding: 0 2.5rem; /* Aumentamos el padding para más espacio */
  background-color: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  z-index: 1000;
}

.dashboard-main {
  flex-grow: 1;
  overflow-y: auto; /* El scroll solo aplicará a esta área */
}
</style>
