<script setup lang="ts">
import { RouterLink } from 'vue-router';
import { authStore } from '@/auth/store';
import { alertStore } from '@/stores/alertStore';

defineOptions({
  name: 'AppSidebar'
});

defineProps<{
  isCollapsed: boolean
}>();
const emit = defineEmits(['toggle-sidebar']);
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-content">
      <div class="sidebar-header">
        <i class="pi pi-shield logo-icon"></i>
        <h2 v-if="!isCollapsed" class="app-title">Embalse IoT</h2>
      </div>
      <nav class="navigation">
        <RouterLink to="/" class="nav-item">
          <i class="pi pi-th-large"></i>
          <span v-if="!isCollapsed">Dashboard</span>
        </RouterLink>

        <RouterLink
          to="/alerts"
          class="nav-item alerts-nav"
          :class="{
            'has-alerts': alertStore.summary.total > 0,
            'has-critical': alertStore.summary.critical > 0
          }"
        >
          <div class="nav-icon-container">
            <!-- Forzar la lógica del icono más explícitamente -->
            <i v-if="alertStore.summary.critical > 0" class="pi pi-exclamation-triangle" style="color: #e53e3e !important;"></i>
            <i v-else-if="alertStore.summary.total > 0" class="pi pi-exclamation-circle" style="color: #ffc107 !important;"></i>
            <i v-else class="pi pi-bell" style="color: #a0aec0 !important;"></i>
            <span v-if="alertStore.summary.total > 0 && !isCollapsed" class="alert-indicator"></span>
            <span v-if="alertStore.summary.total > 0 && isCollapsed" class="alert-badge-collapsed">
              {{ alertStore.summary.total }}
            </span>
          </div>
          <span v-if="!isCollapsed">
            Alertas
            <span
              class="alert-count"
              :class="{
                'alert-count-critical': alertStore.summary.critical > 0,
                'alert-count-warning': alertStore.summary.warning > 0 && alertStore.summary.critical === 0,
                'alert-count-normal': alertStore.summary.total === 0
              }"
            >
              ({{ alertStore.summary.total }})
            </span>
          </span>
        </RouterLink>

        <RouterLink to="/users" class="nav-item" v-if="authStore.user?.role === 'admin'">
          <i class="pi pi-users"></i>
          <span v-if="!isCollapsed">Usuarios</span>
        </RouterLink>
      </nav>
    </div>

    <div class="sidebar-footer">
      <button class="toggle-btn" @click="emit('toggle-sidebar')" title="Colapsar/Expandir Menú">
        <i class="pi" :class="isCollapsed ? 'pi-align-right' : 'pi-align-left'"></i>
      </button>
    </div>
  </aside>
</template>

<style scoped>
:root {
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 88px;
}

.sidebar {
  width: var(--sidebar-width);
  background-color: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  transition: width 0.3s ease-in-out;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0 1.75rem;
  height: var(--header-height, 80px);
  flex-shrink: 0;
  overflow: hidden;
  border-bottom: 1px solid #4a5568;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 0;
}

.logo-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
}

.app-title {
  font-size: 1.2rem;
  font-weight: 600;
  white-space: nowrap;
}

.navigation {
  padding: 1rem;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 0.9rem 1rem;
  color: #a0aec0;
  text-decoration: none;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-item i {
  font-size: 1.5rem;
  margin-right: 1.5rem;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
}

.sidebar.collapsed .nav-item i {
  margin-right: 0;
}

.sidebar.collapsed .nav-item span {
  display: none;
}

.nav-item:hover {
  background-color: #34495e;
  color: #fff;
}

/* --- CORRECCIÓN PARA EL ENLACE ACTIVO --- */
/* Vue Router añade esta clase automáticamente al enlace EXACTO */
.nav-item.router-link-exact-active {
  background-color: #3498db;
  color: #fff;
  font-weight: 500;
}

/* --- NUEVOS ESTILOS PARA EL BOTÓN EN EL FOOTER --- */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #4a5568;
}

.toggle-btn {
  width: 100%;
  background-color: #34495e;
  border: none;
  color: #a0aec0;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  background-color: #4a5568;
  color: #fff;
}

/* --- ESTILOS PARA ALERTAS EN SIDEBAR --- */
.alerts-nav {
  position: relative;
}

.nav-icon-container {
  position: relative;
  display: flex;
  align-items: center;
}

/* Estilos del icono según el estado - MAS ESPECIFICOS */
.alerts-nav .nav-icon-container .pi-bell {
  color: #a0aec0 !important; /* Gris normal cuando no hay alertas */
}

.alerts-nav.has-alerts .nav-icon-container .pi-exclamation-circle {
  color: #ffc107 !important; /* Amarillo para advertencias */
}

.alerts-nav.has-critical .nav-icon-container .pi-exclamation-triangle {
  color: #e53e3e !important; /* Rojo para críticas */
  animation: pulse-icon 2s infinite;
}

/* Asegurar que el icono por defecto NO sea rojo */
.alerts-nav .nav-icon-container i {
  color: #a0aec0; /* Color por defecto gris */
}

.alert-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background-color: #e53e3e;
  border-radius: 50%;
  animation: pulse-dot 2s infinite;
}

.alert-badge-collapsed {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: #e53e3e;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border: 2px solid #2c3e50;
}

.alert-count {
  font-weight: bold;
  margin-left: 0.5rem;
}

/* Colores condicionales para el contador */
.alert-count-normal {
  color: #a0aec0 !important; /* Gris cuando no hay alertas */
}

.alert-count-warning {
  color: #ffc107 !important; /* Amarillo para advertencias */
}

.alert-count-critical {
  color: #e53e3e !important; /* Rojo para críticas */
}

/* Hacer que el item de alertas se destaque cuando hay alertas */
.alerts-nav.has-alerts {
  background-color: rgba(255, 193, 7, 0.1);
  border-left: 3px solid #ffc107;
}

.alerts-nav.has-critical {
  background-color: rgba(229, 62, 62, 0.1);
  border-left: 3px solid #e53e3e;
}

/* Animaciones */
@keyframes pulse-dot {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes pulse-icon {
  0%, 100% {
    color: #e53e3e;
    transform: scale(1);
  }
  50% {
    color: #ff6b6b;
    transform: scale(1.05);
  }
}
</style>
