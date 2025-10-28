<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import type { PropType } from 'vue';
import type { User } from '@/types';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

defineOptions({
  name: 'EditUserModal'
});

const props = defineProps({
  user: {
    type: Object as PropType<User>,
    required: true
  }
});

const emit = defineEmits(['close', 'user-updated']);

const fullName = ref('');
const role = ref(''); // Cambiado a string vacío, será 'operario' o 'admin'
const disabled = ref(false);
const error = ref('');
const isLoading = ref(false);

// Esta función inicializa los valores del formulario
function initializeForm() {
  if (props.user) {
    fullName.value = props.user.full_name;
    role.value = props.user.role;
    disabled.value = props.user.disabled;
  }
}

// Usamos watch para reaccionar a los cambios en props.user
// Esto es crucial si el modal se reutiliza o si la prop user cambia mientras el modal está abierto
watch(() => props.user, (newUser) => {
  if (newUser) {
    initializeForm();
  }
}, { immediate: true }); // immediate: true para que se ejecute al montar también

// onMounted solo para asegurar que se inicializa al principio si watch no lo hace por alguna razón
onMounted(() => {
  initializeForm();
});

async function handleUpdate() {
  isLoading.value = true;
  error.value = '';
  const token = localStorage.getItem('userToken');

  if (!props.user.id) {
    error.value = "Error: ID de usuario no disponible para la actualización.";
    isLoading.value = false;
    return;
  }

  try {
    // ✅ CAMBIAR URL
    const response = await fetch(`${API_BASE_URL}/api/users/${props.user.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        full_name: fullName.value,
        role: role.value,
        disabled: disabled.value
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'No se pudo actualizar el usuario.');
    }

    emit('user-updated');
    emit('close'); // Cerrar el modal después de actualizar

  } catch (e: unknown) { // Manejo de error unknown
    if (e instanceof Error) {
      error.value = e.message;
    } else {
      error.value = String(e);
    }
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="fixed top-0 left-0 w-full h-full bg-black/60 backdrop-blur-sm flex justify-center items-center z-[1000]" @click.self="emit('close')">
    <div class="bg-white p-8 rounded-xl w-[90%] max-w-[500px] shadow-2xl border border-gray-200">
      <!-- Header -->
      <div class="flex items-center gap-3 mb-2 pb-4 border-b border-gray-200">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-md">
          <i class="pi pi-user-edit text-base text-white"></i>
        </div>
        <div class="flex-1">
          <h2 class="text-xl font-bold text-gray-900">Editar Usuario</h2>
          <p class="text-sm text-gray-500 mt-0.5">{{ user.email }}</p>
        </div>
      </div>

      <form @submit.prevent="handleUpdate" class="mt-6">
        <div v-if="error" class="text-red-700 mb-4 p-3 bg-red-50 rounded-lg border border-red-200 text-sm">{{ error }}</div>

        <div class="mb-4">
          <label for="fullName" class="block mb-2 text-sm font-semibold text-gray-700">Nombre Completo</label>
          <input
            id="fullName"
            v-model="fullName"
            type="text"
            required
            class="w-full px-4 py-2.5 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
          >
        </div>

        <div class="mb-4">
          <label for="role" class="block mb-2 text-sm font-semibold text-gray-700">Rol</label>
          <select
            id="role"
            v-model="role"
            class="w-full px-4 py-2.5 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white"
          >
            <option value="operario">Operario</option>
            <option value="admin">Administrador</option>
          </select>
        </div>

        <div class="flex items-center gap-3 mb-6 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <input
            id="disabled"
            v-model="disabled"
            type="checkbox"
            class="w-4 h-4 cursor-pointer accent-blue-600 rounded"
          >
          <label for="disabled" class="text-sm font-medium text-gray-700 cursor-pointer">Usuario Deshabilitado</label>
        </div>

        <div class="mt-6 flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            @click="emit('close')"
            class="px-6 py-2.5 rounded-lg font-semibold text-sm cursor-pointer bg-gray-100 text-gray-700 hover:bg-gray-200 transition-all border border-gray-300"
          >
            Cancelar
          </button>
          <button
            type="submit"
            class="px-6 py-2.5 rounded-lg font-semibold text-sm cursor-pointer bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 transition-all shadow-md hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="isLoading"
          >
            <i v-if="isLoading" class="pi pi-spin pi-spinner mr-2"></i>
            {{ isLoading ? 'Guardando...' : 'Guardar Cambios' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
