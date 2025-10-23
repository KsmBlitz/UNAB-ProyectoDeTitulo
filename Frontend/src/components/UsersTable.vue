<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { Ref } from 'vue';
import type { User } from '@/types';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

defineOptions({
  name: 'UsersTable'
});

const emit = defineEmits(['edit-user', 'delete-user']);

const users: Ref<User[]> = ref([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  await fetchUsers();
});

async function fetchUsers() {
  isLoading.value = true;
  error.value = null;
  const token = localStorage.getItem('userToken');
  if (!token) {
    error.value = "No estás autenticado.";
    isLoading.value = false;
    return;
  }
  try {
    // ✅ CAMBIAR URL
    const response = await fetch(`${API_BASE_URL}/api/users`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Error ${response.status}`);
    }
    const dataFromApi = await response.json();
    // Nos aseguramos que el ID esté como 'id' en el frontend
    users.value = dataFromApi.map((user: unknown) => {
      const typedUser = user as User & { _id?: string };
      return { ...typedUser, id: typedUser.id || typedUser._id };
    });
  } catch (e: unknown) {
    if (e instanceof Error) {
      error.value = e.message;
    } else {
      error.value = String(e);
    }
  } finally {
    isLoading.value = false;
  }
}

defineExpose({
  fetchUsers
});
</script>

<template>
  <div class="bg-white rounded-lg p-6 shadow-sm mt-8">
    <div v-if="isLoading" class="text-center py-8 text-gray-500">Cargando usuarios...</div>
    <div v-else-if="error" class="text-danger-500 font-bold">{{ error }}</div>
    <div v-else-if="users.length > 0" class="overflow-x-auto">
      <table class="w-full border-collapse">
        <thead>
          <tr>
            <th class="p-4 text-left border-b border-gray-200 text-gray-500 font-medium text-sm uppercase">Nombre Completo</th>
            <th class="p-4 text-left border-b border-gray-200 text-gray-500 font-medium text-sm uppercase">Email</th>
            <th class="p-4 text-left border-b border-gray-200 text-gray-500 font-medium text-sm uppercase">Rol</th>
            <th class="p-4 text-left border-b border-gray-200 text-gray-500 font-medium text-sm uppercase">Estado</th>
            <th class="p-4 text-left border-b border-gray-200 text-gray-500 font-medium text-sm uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50 transition-colors">
            <td class="p-4 border-b border-gray-200">{{ user.full_name }}</td>
            <td class="p-4 border-b border-gray-200">{{ user.email }}</td>
            <td class="p-4 border-b border-gray-200 capitalize">{{ user.role }}</td>
            <td class="p-4 border-b border-gray-200">
              <span
                class="px-3 py-1 rounded-full text-sm font-medium capitalize"
                :class="user.disabled ? 'bg-gray-200 text-gray-600' : 'bg-success-100 text-success-700'"
              >
                {{ user.disabled ? 'Deshabilitado' : 'Activo' }}
              </span>
            </td>
            <td class="p-4 border-b border-gray-200">
              <button
                @click="emit('edit-user', user)"
                class="mr-2 px-3 py-1.5 border border-gray-300 bg-gray-100 rounded hover:bg-gray-200 font-medium transition-colors"
              >
                Editar
              </button>
              <button
                @click="emit('delete-user', user)"
                class="px-3 py-1.5 border border-danger-500 text-danger-500 bg-white rounded hover:bg-danger-500 hover:text-white font-medium transition-colors"
              >
                Eliminar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-8 text-gray-500">No se encontraron usuarios.</div>
  </div>
</template>
