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
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h2>Editar Usuario</h2>
      <p class="user-email">{{ user.email }}</p>
      <form @submit.prevent="handleUpdate">
        <div v-if="error" class="error-message">{{ error }}</div>
        <div class="form-group">
          <label for="fullName">Nombre Completo</label>
          <input id="fullName" v-model="fullName" type="text" required>
        </div>
        <div class="form-group">
          <label for="role">Rol</label>
          <select id="role" v-model="role">
            <option value="operario">Operario</option>
            <option value="admin">Administrador</option>
          </select>
        </div>
        <div class="form-group-checkbox">
          <input id="disabled" v-model="disabled" type="checkbox">
          <label for="disabled">Usuario Deshabilitado</label>
        </div>
        <div class="form-actions">
          <button type="button" @click="emit('close')" class="btn-cancel">Cancelar</button>
          <button type="submit" class="btn-submit" :disabled="isLoading">
            {{ isLoading ? 'Guardando...' : 'Guardar Cambios' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* Estilos sin cambios */
.modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background-color:rgba(0,0,0,.5);display:flex;justify-content:center;align-items:center;z-index:1000}.modal-content{background:#fff;padding:2rem;border-radius:8px;width:90%;max-width:500px;box-shadow:0 5px 15px rgba(0,0,0,.3)}.modal-content h2{margin-top:0}.user-email{color:#6c757d;margin-top:-1rem;margin-bottom:1.5rem;display:block}.form-group{margin-bottom:1rem}.form-group label{display:block;margin-bottom:.5rem}.form-group input,.form-group select{width:100%;padding:.5rem;font-size:1rem;border-radius:4px;border:1px solid #ccc;box-sizing:border-box}.form-group-checkbox{display:flex;align-items:center;gap:.5rem;margin-bottom:1rem}.form-actions{margin-top:1.5rem;display:flex;justify-content:flex-end;gap:1rem}.btn-submit,.btn-cancel{padding:.75rem 1.5rem;border:none;border-radius:6px;font-weight:700;cursor:pointer}.btn-cancel{background-color:#6c757d;color:#fff}.btn-submit{background-color:#007bff;color:#fff}.btn-submit:disabled{background-color:#aaa}.error-message{color:red;margin-bottom:1rem}
</style>
