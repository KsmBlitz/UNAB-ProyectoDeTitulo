<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import { jwtDecode } from 'jwt-decode';
import { authStore } from '@/auth/store';
import AuthLayout from '@/components/AuthLayout.vue';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

defineOptions({
  name: 'LoginView'
});

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const router = useRouter();

const handleLogin = async () => {
  errorMessage.value = '';

  const formData = new URLSearchParams();
  formData.append('username', email.value);
  formData.append('password', password.value);

  try {
    const response = await fetch(`${API_BASE_URL}/api/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error de autenticación');
    }

    const data = await response.json();
    localStorage.setItem('userToken', data.access_token);

    const userResponse = await fetch(`${API_BASE_URL}/api/users/me`, {
      headers: {
        'Authorization': `Bearer ${data.access_token}`
      }
    });

    if (userResponse.ok) {
      const userData = await userResponse.json();
      authStore.user = {
        email: userData.email,
        role: userData.role,
        full_name: userData.full_name
      };
    } else {
      const decodedToken: { sub: string; role: string } = jwtDecode(data.access_token);
      authStore.user = {
        email: decodedToken.sub,
        role: decodedToken.role
      };
    }

    router.push('/');

  } catch (error: unknown) {
    if (error instanceof Error) {
      errorMessage.value = error.message || 'No se pudo conectar con el servidor.';
    } else {
      errorMessage.value = 'No se pudo conectar con el servidor.';
    }
    password.value = '';
  }
};
</script>

<template>
  <!-- ✅ USAR EL NUEVO LAYOUT BASE -->
  <AuthLayout title="Embalses IoT" subtitle="Sistema de monitoreo">
    <form @submit.prevent="handleLogin" class="login-form">
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

      <div class="form-group">
        <label for="email">Correo Electrónico</label>
        <input type="email" id="email" v-model="email" required placeholder="admin@embalses.cl">
      </div>

      <div class="form-group">
        <label for="password">Contraseña</label>
        <input type="password" id="password" v-model="password" required placeholder="********">
      </div>

      <button type="submit" class="login-button">Iniciar Sesión</button>

      <div class="form-footer">
        <RouterLink to="/forgot-password" class="forgot-password-link">
          ¿Olvidaste tu contraseña?
        </RouterLink>
      </div>
    </form>
  </AuthLayout>
</template>

<style scoped>
/* Solo estilos específicos del formulario */
.login-form { display: flex; flex-direction: column; }
.form-group { margin-bottom: 1.5rem; text-align: left; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #34495e; }
.form-group input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
}
.login-button {
  width: 100%;
  padding: 0.85rem 1.5rem;
  background-color: #3498db;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}
.login-button:hover { background-color: #2980b9; }
.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}
.form-footer { margin-top: 1.5rem; text-align: center; }
.forgot-password-link { color: #3498db; text-decoration: none; font-size: 0.9rem; }
.forgot-password-link:hover { text-decoration: underline; }
</style>
