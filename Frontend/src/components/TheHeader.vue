<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { authStore } from '@/auth/store'; // Importar el store de autenticación

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

// 4. Lógica para cerrar el menú al hacer clic fuera
const handleClickOutside = (event: MouseEvent) => {
  if (userProfileRef.value && !userProfileRef.value.contains(event.target as Node)) {
    isMenuOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
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
      <div class="notifications">
        <i class="pi pi-bell notification-icon"></i>
        <span class="notification-badge">2</span>
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
.header-container{display:flex;justify-content:space-between;align-items:center;padding:.75rem 1.5rem;background-color:#fff;border-bottom:1px solid #e9ecef;flex-shrink:0}.header-left,.header-right{display:flex;align-items:center;gap:1.5rem}.location-selector{display:flex;align-items:center;gap:.5rem;border:1px solid #ced4da;padding:.5rem 1rem;border-radius:6px;cursor:pointer}.notifications{position:relative;cursor:pointer}.notification-icon{font-size:1.5rem}.notification-badge{position:absolute;top:-5px;right:-5px;background-color:#d9534f;color:#fff;border-radius:50%;width:20px;height:20px;font-size:.75rem;display:flex;justify-content:center;align-items:center;font-weight:700}.user-avatar{width:40px;height:40px;border-radius:50%;background-color:#f1f1f1;display:flex;justify-content:center;align-items:center}.user-avatar .pi-user{font-size:1.25rem;color:#555}.user-info{display:flex;flex-direction:column;align-items:flex-start}.user-name{font-weight:700;font-size:.875rem}.user-role{font-size:.75rem;color:#6c757d}

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
