<script setup lang="ts">
import { ref } from 'vue';
import type { Ref } from 'vue';
import UsersTable from '@/components/UsersTable.vue';
import CreateUserModal from '@/components/CreateUserModal.vue';
import EditUserModal from '@/components/EditUserModal.vue';
import { API_BASE_URL } from '@/config/api';
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
    <!-- Header Card -->
    <div class="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 mb-6 shadow-lg">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
            <i class="pi pi-users text-2xl text-white"></i>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-white m-0">Gestión de Usuarios</h1>
            <p class="text-blue-100 text-sm mt-1">Administra los usuarios del sistema</p>
          </div>
        </div>
        <button
          @click="isCreateModalOpen = true"
          class="bg-white text-blue-600 rounded-lg px-5 py-2.5 text-sm font-semibold cursor-pointer flex items-center gap-2 hover:bg-blue-50 transition-all shadow-md hover:shadow-lg"
        >
          <i class="pi pi-plus text-sm"></i>
          <span>Crear Nuevo Usuario</span>
        </button>
      </div>
    </div>

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
