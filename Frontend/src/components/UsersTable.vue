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
  <div class="users-table-card">
    <div v-if="isLoading">Cargando usuarios...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <table v-else-if="users.length > 0">
      <thead>
        <tr>
          <th>Nombre Completo</th>
          <th>Email</th>
          <th>Rol</th>
          <th>Estado</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.full_name }}</td>
          <td>{{ user.email }}</td>
          <td>{{ user.role }}</td>
          <td>
            <span class="status-pill" :class="user.disabled ? 'status-inactive' : 'status-active'">
              {{ user.disabled ? 'Deshabilitado' : 'Activo' }}
            </span>
          </td>
          <td>
            <button @click="emit('edit-user', user)" class="action-btn">Editar</button>
            <button @click="emit('delete-user', user)" class="action-btn-delete">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else>No se encontraron usuarios.</div>
  </div>
</template>

<style scoped>
/* Estilos sin cambios */
.status-pill{padding:.25rem .75rem;border-radius:9999px;font-size:.875rem;font-weight:500;text-transform:capitalize}.status-active{background-color:#d4edda;color:#155724}.status-inactive{background-color:#e9ecef;color:#6c757d}.users-table-card{background-color:#fff;border-radius:8px;padding:1.5rem;box-shadow:0 2px 4px rgba(0,0,0,.05);margin-top:2rem}.error-message{color:#d9534f;font-weight:700}table{width:100%;border-collapse:collapse}th,td{padding:1rem;text-align:left;border-bottom:1px solid #e9ecef}thead th{color:#6c757d;font-weight:500;font-size:.875rem;text-transform:uppercase}tbody tr:last-child td{border-bottom:none}.action-btn,.action-btn-delete{margin-right:.5rem;padding:.35rem .75rem;border:1px solid #ced4da;background-color:#f8f9fa;border-radius:4px;cursor:pointer;font-weight:500;transition:background-color .2s}.action-btn:hover{background-color:#e2e6ea}.action-btn-delete{border-color:#d9534f;color:#d9534f}.action-btn-delete:hover{background-color:#d9534f;color:#fff}
</style>
