<script setup lang="ts">
import { ref } from 'vue';
import type { Ref } from 'vue';
import UsersTable from '@/components/UsersTable.vue';
import CreateUserModal from '@/components/CreateUserModal.vue';
import EditUserModal from '@/components/EditUserModal.vue';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT
import type { User } from '@/types';

defineOptions({
  name: 'UserManagementView'
});

// ---- Lógica para Modales ----
const isCreateModalOpen = ref(false);
const isEditModalOpen = ref(false);

// userToEdit debe ser del tipo User o null
const userToEdit: Ref<User | null> = ref(null);

// Aseguramos que el usuario que pasamos tiene un ID válido
function openEditModal(user: User) {
  // Asegurarse de que el ID es un string antes de asignarlo al reactive userToEdit
  userToEdit.value = { ...user, id: String(user.id) };
  isEditModalOpen.value = true;
}

// ---- Lógica para Recargar la Tabla ----
const usersTableRef = ref<InstanceType<typeof UsersTable> | null>(null);

function refreshTable() {
  usersTableRef.value?.fetchUsers();
}

function handleUserCreated() {
  isCreateModalOpen.value = false;
  refreshTable();
}

function handleUserUpdated() {
  isEditModalOpen.value = false;
  refreshTable();
}

// ---- Lógica para Borrar Usuario ----
async function handleDeleteUser(user: User) {
  if (!confirm(`¿Estás seguro de que quieres eliminar a ${user.full_name}? Esta acción no se puede deshacer.`)) {
    return;
  }

  const token = localStorage.getItem('userToken');
  const userIdToDelete = String(user.id);

  try {
    // ✅ CAMBIAR URL
    const response = await fetch(`${API_BASE_URL}/api/users/${userIdToDelete}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'No se pudo eliminar el usuario.');
    }
    alert('Usuario eliminado exitosamente.');
    refreshTable();
  } catch (e: unknown) { // Correcto manejo de error unknown
    if (e instanceof Error) {
      alert(`Error: ${e.message}`);
    } else {
      alert(`Error desconocido: ${String(e)}`);
    }
  }
}
</script>

<template>
  <div class="view-container">
    <header class="view-header">
      <h1>Gestión de Usuarios</h1>
      <button @click="isCreateModalOpen = true" class="add-user-btn">
        <i class="pi pi-plus"></i>
        <span>Crear Nuevo Usuario</span>
      </button>
    </header>
    <p>Desde aquí podrás administrar los usuarios del sistema.</p>

    <UsersTable
      ref="usersTableRef"
      @edit-user="openEditModal"
      @delete-user="handleDeleteUser"
    />

    <CreateUserModal
      v-if="isCreateModalOpen"
      @close="isCreateModalOpen = false"
      @user-created="handleUserCreated"
    />
    <EditUserModal
      v-if="isEditModalOpen && userToEdit"
      :user="userToEdit"
      @close="isEditModalOpen = false"
      @user-updated="handleUserUpdated"
    />
  </div>
</template>

<style scoped>
/* Estilos sin cambios */
.view-container{padding:2rem}.view-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}.view-header h1{margin:0}.add-user-btn{background-color:#28a745;color:#fff;border:none;border-radius:6px;padding:.75rem 1rem;font-size:1rem;font-weight:500;cursor:pointer;display:flex;align-items:center;gap:.5rem}.add-user-btn:hover{background-color:#218838}
</style>
