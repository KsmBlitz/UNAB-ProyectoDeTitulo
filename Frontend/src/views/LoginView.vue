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
  <AuthLayout title="Embalses IoT" subtitle="Sistema de monitoreo">
    <form @submit.prevent="handleLogin" class="flex flex-col">
      <!-- Error message with icon -->
      <div v-if="errorMessage" class="bg-danger-50 text-danger-700 px-4 py-3 rounded-lg mb-6 border border-danger-200 flex items-start gap-3 animate-shake">
        <i class="pi pi-exclamation-circle text-lg mt-0.5"></i>
        <span class="flex-1 text-left">{{ errorMessage }}</span>
      </div>

      <!-- Email field with icon -->
      <div class="mb-6 text-left">
        <label for="email" class="block mb-2.5 font-semibold text-gray-700 text-sm tracking-wide">
          Correo Electrónico
        </label>
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <i class="pi pi-envelope text-gray-400"></i>
          </div>
          <input
            type="email"
            id="email"
            v-model="email"
            required
            placeholder="admin@embalses.cl"
            class="w-full pl-11 pr-4 py-3.5 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-400"
          >
        </div>
      </div>

      <!-- Password field with icon -->
      <div class="mb-2 text-left">
        <label for="password" class="block mb-2.5 font-semibold text-gray-700 text-sm tracking-wide">
          Contraseña
        </label>
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <i class="pi pi-lock text-gray-400"></i>
          </div>
          <input
            type="password"
            id="password"
            v-model="password"
            required
            placeholder="••••••••"
            class="w-full pl-11 pr-4 py-3.5 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-400"
          >
        </div>
      </div>

      <!-- Forgot password link -->
      <div class="mb-6 text-right">
        <RouterLink to="/forgot-password" class="text-blue-600 no-underline text-sm hover:text-blue-700 hover:underline transition-colors">
          ¿Olvidaste tu contraseña?
        </RouterLink>
      </div>

      <!-- Submit button with hover effect -->
      <button
        type="submit"
        class="w-full px-6 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white border-none rounded-lg text-base font-semibold cursor-pointer hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
      >
        <i class="pi pi-sign-in"></i>
        <span>Iniciar Sesión</span>
      </button>
    </form>
  </AuthLayout>
</template>
