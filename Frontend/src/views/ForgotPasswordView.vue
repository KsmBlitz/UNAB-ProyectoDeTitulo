<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink } from 'vue-router';
import AuthLayout from '@/components/AuthLayout.vue';

defineOptions({
  name: 'ForgotPasswordView'
});

const email = ref('');
const message = ref('');
const error = ref('');
const isLoading = ref(false);
const isSuccess = ref(false);

const handleSubmit = async () => {
  if (!email.value.trim()) {
    error.value = 'Por favor ingresa tu correo electrónico';
    return;
  }

  // Validación básica de email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email.value)) {
    error.value = 'Por favor ingresa un correo electrónico válido';
    return;
  }

  isLoading.value = true;
  error.value = '';
  message.value = '';

  try {
    const response = await fetch('http://127.0.0.1:8000/api/auth/forgot-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value.trim().toLowerCase()
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al procesar la solicitud');
    }

    const data = await response.json();
    message.value = data.message;
    isSuccess.value = true;

  } catch (err: unknown) {
    if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = 'Error de conexión. Por favor intenta nuevamente.';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <!-- ✅ USAR EL NUEVO LAYOUT BASE -->
  <AuthLayout title="Recuperar Contraseña">
    <div v-if="isSuccess" class="text-center">
      <div class="mb-6 inline-flex items-center justify-center w-20 h-20 bg-success-100 rounded-full">
        <i class="pi pi-check-circle text-4xl text-success-600"></i>
      </div>
      <h3 class="mb-3 text-gray-800 text-2xl font-bold">Solicitud Enviada</h3>
      <p class="mb-8 text-gray-600 leading-relaxed text-lg">{{ message }}</p>

      <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl mb-8 text-left border border-blue-200">
        <h4 class="m-0 mb-4 text-gray-800 font-semibold flex items-center gap-2">
          <i class="pi pi-list-check text-blue-600"></i>
          Próximos pasos
        </h4>
        <ol class="m-0 pl-6 space-y-3">
          <li class="text-gray-700">Revisa tu bandeja de entrada en <strong class="text-blue-700">{{ email }}</strong></li>
          <li class="text-gray-700">Si no encuentras el email, revisa tu carpeta de spam</li>
          <li class="text-gray-700">Haz clic en el enlace del email para cambiar tu contraseña</li>
          <li class="text-gray-700">El enlace expirará en <strong>1 hora</strong> por seguridad</li>
        </ol>
      </div>

      <div class="flex gap-3 justify-center flex-wrap">
        <RouterLink
          to="/login"
          class="inline-flex items-center gap-2 px-6 py-3.5 no-underline rounded-lg font-semibold transition-all duration-200 bg-gradient-to-r from-success-600 to-success-700 text-white hover:from-success-700 hover:to-success-800 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          <i class="pi pi-arrow-left"></i>
          Volver al inicio de sesión
        </RouterLink>
        <button
          @click="isSuccess = false; email = ''; message = ''"
          class="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg font-semibold transition-all duration-200 bg-gray-200 text-gray-700 border-none cursor-pointer hover:bg-gray-300 shadow-md hover:shadow-lg"
        >
          <i class="pi pi-refresh"></i>
          Intentar con otro email
        </button>
      </div>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="flex flex-col">
      <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl mb-8 text-left border border-blue-200">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <i class="pi pi-lock text-white text-lg"></i>
          </div>
          <div>
            <h3 class="m-0 mb-2 text-gray-800 font-semibold text-lg">¿Olvidaste tu contraseña?</h3>
            <p class="m-0 text-gray-600 leading-relaxed text-sm">No te preocupes. Ingresa tu correo electrónico y te enviaremos un enlace seguro para crear una nueva contraseña.</p>
          </div>
        </div>
      </div>

      <div v-if="error" class="bg-danger-50 text-danger-700 border border-danger-200 px-4 py-3.5 mb-6 rounded-lg flex items-start gap-3 animate-shake">
        <i class="pi pi-exclamation-triangle text-lg mt-0.5"></i>
        <span>{{ error }}</span>
      </div>

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
            placeholder="tu@ejemplo.com"
            :disabled="isLoading"
            autocomplete="email"
            class="w-full pl-11 pr-4 py-3.5 border border-gray-300 rounded-lg text-base transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:opacity-70 hover:border-gray-400"
          >
        </div>
      </div>

      <button
        type="submit"
        class="w-full px-6 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white border-none rounded-lg text-base font-semibold cursor-pointer transition-all duration-200 mt-2 flex items-center justify-center gap-2 hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
        :disabled="isLoading || !email.trim()"
      >
        <i v-if="isLoading" class="pi pi-spin pi-spinner"></i>
        <i v-else class="pi pi-send"></i>
        {{ isLoading ? 'Enviando...' : 'Enviar Enlace de Recuperación' }}
      </button>

      <div class="flex items-start gap-3 mt-6 px-4 py-3.5 bg-blue-50 rounded-lg text-blue-700 border border-blue-200">
        <i class="pi pi-info-circle mt-0.5"></i>
        <small class="leading-relaxed">Por seguridad, el enlace expirará en <strong>1 hora</strong> y solo funcionará una vez.</small>
      </div>

      <div class="mt-8 text-center">
        <RouterLink
          to="/login"
          class="text-gray-600 no-underline inline-flex items-center justify-center gap-2 text-sm hover:text-blue-600 transition-colors"
        >
          <i class="pi pi-arrow-left"></i>
          Volver al inicio de sesión
        </RouterLink>
      </div>
    </form>
  </AuthLayout>
</template>
