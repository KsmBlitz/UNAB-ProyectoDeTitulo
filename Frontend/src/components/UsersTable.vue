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
  <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
    <div v-if="isLoading" class="flex items-center justify-center gap-2 py-12 text-gray-500">
      <i class="pi pi-spin pi-spinner text-lg"></i>
      <span class="text-sm">Cargando usuarios...</span>
    </div>
    <div v-else-if="error" class="text-red-700 font-semibold p-4 bg-red-50 rounded-lg border border-red-200">{{ error }}</div>
    <div v-else-if="users.length > 0" class="overflow-x-auto rounded-lg border border-gray-200">
      <table class="w-full border-collapse">
        <thead>
          <tr class="bg-gradient-to-r from-slate-50 to-gray-100">
            <th class="p-4 text-left border-b border-gray-300 text-gray-700 font-semibold text-xs uppercase tracking-wider">Nombre Completo</th>
            <th class="p-4 text-left border-b border-gray-300 text-gray-700 font-semibold text-xs uppercase tracking-wider">Email</th>
            <th class="p-4 text-left border-b border-gray-300 text-gray-700 font-semibold text-xs uppercase tracking-wider">Rol</th>
            <th class="p-4 text-left border-b border-gray-300 text-gray-700 font-semibold text-xs uppercase tracking-wider">Estado</th>
            <th class="p-4 text-left border-b border-gray-300 text-gray-700 font-semibold text-xs uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white">
          <tr v-for="user in users" :key="user.id" class="hover:bg-blue-50/50 transition-colors">
            <td class="p-4 border-b border-gray-100 text-gray-900 font-medium">{{ user.full_name }}</td>
            <td class="p-4 border-b border-gray-100 text-gray-600 text-sm">{{ user.email }}</td>
            <td class="p-4 border-b border-gray-100">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 capitalize">
                <i class="pi" :class="user.role === 'admin' ? 'pi-shield' : 'pi-user'"></i>
                {{ user.role }}
              </span>
            </td>
            <td class="p-4 border-b border-gray-100">
              <span
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold"
                :class="user.disabled ? 'bg-gray-50 text-gray-700 border border-gray-200' : 'bg-green-50 text-green-700 border border-green-200'"
              >
                <i class="pi text-[6px]" :class="user.disabled ? 'pi-circle-fill' : 'pi-circle-fill'"></i>
                {{ user.disabled ? 'Deshabilitado' : 'Activo' }}
              </span>
            </td>
            <td class="p-4 border-b border-gray-100">
              <div class="flex gap-2">
                <button
                  @click="emit('edit-user', user)"
                  class="px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium text-sm transition-all shadow-sm hover:shadow-md flex items-center gap-1.5"
                >
                  <i class="pi pi-pencil text-xs"></i>
                  Editar
                </button>
                <button
                  @click="emit('delete-user', user)"
                  class="px-3 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 font-medium text-sm transition-all shadow-sm hover:shadow-md flex items-center gap-1.5"
                >
                  <i class="pi pi-trash text-xs"></i>
                  Eliminar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-12 text-gray-500">
      <i class="pi pi-users text-4xl mb-3 text-gray-300"></i>
      <p class="text-sm">No se encontraron usuarios.</p>
    </div>
  </div>
</template>
