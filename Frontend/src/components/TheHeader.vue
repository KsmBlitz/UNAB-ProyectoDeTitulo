<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { authStore } from '@/auth/store'; // Importar el store de autenticación
import { alertStore } from '@/stores/alertStore'; // Importar el store de alertas

defineOptions({
  name: 'TheHeader'
});

// Eliminar las variables estáticas
// const userName = 'Usuario A';
// const userRole = 'Administrador';

const router = useRouter();

// 1. Estado para controlar la visibilidad del menú
const isMenuOpen = ref(false);
const userProfileRef = ref<HTMLDivElement | null>(null);

// 2. Función para abrir/cerrar el menú
function toggleUserMenu() {
  isMenuOpen.value = !isMenuOpen.value;
}

// 3. Función para cerrar sesión
function handleLogout() {
  console.log('Cerrando sesión...');
  localStorage.removeItem('userToken');
  // Limpiar el store al cerrar sesión
  authStore.user = null;
  router.push('/login');
}

// 4. Función para navegar a alertas
function navigateToAlerts() {
  router.push('/alerts');
}

// 5. Computadas para alertas
const alertSummary = computed(() => alertStore.summary);
const hasAlerts = computed(() => alertSummary.value.total > 0);
const hasCriticalAlerts = computed(() => alertSummary.value.critical > 0);

// 4. Lógica para cerrar el menú al hacer clic fuera
const handleClickOutside = (event: MouseEvent) => {
  if (userProfileRef.value && !userProfileRef.value.contains(event.target as Node)) {
    isMenuOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  // Inicializar store de alertas
  alertStore.startPolling();
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  // Detener polling de alertas
  alertStore.stopPolling();
});
</script>

<template>
  <header class="header-container">
    <div class="header-left">
      <div class="location-selector">
        <i class="pi pi-map-marker"></i>
        <span>Ubicación</span>
        <i class="pi pi-chevron-down"></i>
      </div>
    </div>

    <div class="header-right">
      <div class="alerts-counter" @click="navigateToAlerts" :class="{ 'has-critical': hasCriticalAlerts }">
        <i class="pi pi-exclamation-triangle alert-icon"></i>
        <span v-if="hasAlerts" class="alert-badge">{{ alertSummary.total }}</span>
      </div>

      <div class="user-profile" @click="toggleUserMenu" ref="userProfileRef">
        <div class="user-avatar">
          <i class="pi pi-user"></i>
        </div>
        <div class="user-info">
          <!-- Usar datos del authStore en lugar de valores estáticos -->
          <span class="user-name">{{ authStore.user?.full_name }}</span>
          <span class="user-role">{{
            authStore.user?.role === 'admin' ? 'Administrador' :
            authStore.user?.role === 'operario' ? 'Operario' :
            'Sin rol'
          }}</span>
        </div>

        <div v-if="isMenuOpen" class="user-menu">
          <div class="menu-header">
            <!-- Usar datos del authStore en el menú también -->
            <span class="user-name">{{ authStore.user?.full_name }}</span>
            <span class="user-email">{{ authStore.user?.email || 'Sin email' }}</span>
          </div>
          <ul>
            <li class="menu-item">
              <i class="pi pi-user-edit"></i>
              <span>Editar Perfil</span>
            </li>
            <li class="menu-item">
              <i class="pi pi-cog"></i>
              <span>Configuración</span>
            </li>
            <li class="menu-item logout" @click="handleLogout">
              <i class="pi pi-sign-out"></i>
              <span>Cerrar Sesión</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
/* --- Estilos existentes (sin cambios) --- */
.header-container{display:flex;justify-content:space-between;align-items:center;padding:.75rem 1.5rem;background-color:#fff;border-bottom:1px solid #e9ecef;flex-shrink:0}.header-left,.header-right{display:flex;align-items:center;gap:1.5rem}.location-selector{display:flex;align-items:center;gap:.5rem;border:1px solid #ced4da;padding:.5rem 1rem;border-radius:6px;cursor:pointer}.alerts-counter{position:relative;cursor:pointer;padding:.5rem;border-radius:6px;transition:all .2s ease}.alerts-counter:hover{background-color:#f8f9fa}.alert-icon{font-size:1.5rem;color:#6c757d;transition:color .2s ease}.alerts-counter.has-critical .alert-icon{color:#dc3545}.alert-badge{position:absolute;top:-5px;right:-5px;background-color:#ffc107;color:#000;border-radius:50%;width:20px;height:20px;font-size:.75rem;display:flex;justify-content:center;align-items:center;font-weight:700}.alerts-counter.has-critical .alert-badge{background-color:#dc3545;color:#fff}.user-avatar{width:40px;height:40px;border-radius:50%;background-color:#f1f1f1;display:flex;justify-content:center;align-items:center}.user-avatar .pi-user{font-size:1.25rem;color:#555}.user-info{display:flex;flex-direction:column;align-items:flex-start}.user-name{font-weight:700;font-size:.875rem}.user-role{font-size:.75rem;color:#6c757d}

/* --- NUEVOS ESTILOS PARA EL MENÚ --- */

.user-profile {
  position: relative; /* Clave para posicionar el menú */
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.user-profile:hover {
  background-color: #f1f1f1;
}

.user-menu {
  position: absolute;
  top: 100%; /* Se posiciona justo debajo del perfil */
  right: 0;
  margin-top: 0.5rem;
  width: 300px;
  background-color: #343a40; /* Fondo oscuro */
  color: #f8f9fa; /* Texto claro */
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  overflow: hidden;
}

.menu-header {
  padding: 1.5rem;
  text-align: center;
  border-bottom: 1px solid #495057;
}

.user-email {
  font-size: 0.875rem;
  color: #adb5bd;
}

.user-menu ul {
  list-style: none;
  padding: 0.5rem;
  margin: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background-color: #495057;
}

.menu-item i {
  font-size: 1.2rem;
  width: 24px;
  text-align: center;
}
</style>
