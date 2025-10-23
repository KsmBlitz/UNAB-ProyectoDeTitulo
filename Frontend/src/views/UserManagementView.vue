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
  <div class="p-8">
    <header class="flex justify-between items-center mb-4">
      <h1 class="text-3xl font-bold text-gray-800 m-0">Gestión de Usuarios</h1>
      <button
        @click="isCreateModalOpen = true"
        class="bg-success-500 text-white border-none rounded-md px-4 py-3 text-base font-medium cursor-pointer flex items-center gap-2 hover:bg-success-600 transition-colors"
      >
        <i class="pi pi-plus"></i>
        <span>Crear Nuevo Usuario</span>
      </button>
    </header>
    <p class="text-gray-600 mb-6">Desde aquí podrás administrar los usuarios del sistema.</p>

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
