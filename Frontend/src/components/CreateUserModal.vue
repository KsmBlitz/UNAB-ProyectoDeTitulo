<script setup lang="ts">
import { ref } from 'vue';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

const emit = defineEmits(['close', 'user-created']);

defineOptions({
  name: 'CreateUserModal'
});

const fullName = ref('');
const email = ref('');
const password = ref('');
const role = ref('operario'); // Rol por defecto
const error = ref('');
const isLoading = ref(false);

async function handleSubmit() {
  isLoading.value = true;
  error.value = '';
  const token = localStorage.getItem('userToken');

  try {
    // ✅ CAMBIAR URL
    const response = await fetch(`${API_BASE_URL}/api/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        full_name: fullName.value,
        email: email.value,
        password: password.value,
        role: role.value
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'No se pudo crear el usuario.');
    }

    // Si todo va bien, emitimos un evento para que el padre sepa
    emit('user-created');

  } catch (e) {
    error.value = (e instanceof Error) ? e.message : String(e);
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="fixed top-0 left-0 w-full h-full bg-black/50 flex justify-center items-center z-[1000]" @click.self="emit('close')">
    <div class="bg-white p-8 rounded-lg w-[90%] max-w-[500px] shadow-2xl">
      <h2 class="mt-0 mb-6 text-2xl font-bold text-gray-800">Crear Nuevo Usuario</h2>
      <form @submit.prevent="handleSubmit">
        <div v-if="error" class="text-danger-500 mb-4 p-3 bg-danger-50 rounded border border-danger-200">{{ error }}</div>
        <div class="mb-4">
          <label for="fullName" class="block mb-2 font-medium text-gray-700">Nombre Completo</label>
          <input
            id="fullName"
            v-model="fullName"
            type="text"
            required
            class="w-full px-4 py-2 text-base rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
        </div>
        <div class="mb-4">
          <label for="email" class="block mb-2 font-medium text-gray-700">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            class="w-full px-4 py-2 text-base rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
        </div>
        <div class="mb-4">
          <label for="password" class="block mb-2 font-medium text-gray-700">Contraseña</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            class="w-full px-4 py-2 text-base rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
        </div>
        <div class="mb-4">
          <label for="role" class="block mb-2 font-medium text-gray-700">Rol</label>
          <select
            id="role"
            v-model="role"
            class="w-full px-4 py-2 text-base rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="operario">Operario</option>
            <option value="admin">Administrador</option>
          </select>
        </div>
        <div class="mt-6 flex justify-end gap-4">
          <button
            type="button"
            @click="emit('close')"
            class="px-6 py-3 border-none rounded-md font-bold cursor-pointer bg-gray-500 text-white hover:bg-gray-600 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            class="px-6 py-3 border-none rounded-md font-bold cursor-pointer bg-success-500 text-white hover:bg-success-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            :disabled="isLoading"
          >
            {{ isLoading ? 'Creando...' : 'Crear Usuario' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
