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
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <h2>Crear Nuevo Usuario</h2>
      <form @submit.prevent="handleSubmit">
        <div v-if="error" class="error-message">{{ error }}</div>
        <div class="form-group">
          <label for="fullName">Nombre Completo</label>
          <input id="fullName" v-model="fullName" type="text" required>
        </div>
        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" required>
        </div>
        <div class="form-group">
          <label for="password">Contraseña</label>
          <input id="password" v-model="password" type="password" required>
        </div>
        <div class="form-group">
          <label for="role">Rol</label>
          <select id="role" v-model="role">
            <option value="operario">Operario</option>
            <option value="admin">Administrador</option>
          </select>
        </div>
        <div class="form-actions">
          <button type="button" @click="emit('close')" class="btn-cancel">Cancelar</button>
          <button type="submit" class="btn-submit" :disabled="isLoading">
            {{ isLoading ? 'Creando...' : 'Crear Usuario' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background-color:rgba(0,0,0,.5);display:flex;justify-content:center;align-items:center;z-index:1000}.modal-content{background:#fff;padding:2rem;border-radius:8px;width:90%;max-width:500px;box-shadow:0 5px 15px rgba(0,0,0,.3)}.modal-content h2{margin-top:0}.form-group{margin-bottom:1rem}.form-group label{display:block;margin-bottom:.5rem}.form-group input,.form-group select{width:100%;padding:.5rem;font-size:1rem;border-radius:4px;border:1px solid #ccc;box-sizing:border-box}.form-actions{margin-top:1.5rem;display:flex;justify-content:flex-end;gap:1rem}.btn-submit,.btn-cancel{padding:.75rem 1.5rem;border:none;border-radius:6px;font-weight:700;cursor:pointer}.btn-cancel{background-color:#6c757d;color:#fff}.btn-submit{background-color:#28a745;color:#fff}.btn-submit:disabled{background-color:#aaa}.error-message{color:red;margin-bottom:1rem}
</style>
