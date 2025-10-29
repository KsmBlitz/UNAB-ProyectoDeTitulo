<!-- filepath: Frontend/src/views/ResetPasswordView.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import AuthLayout from '@/components/AuthLayout.vue';

defineOptions({
  name: 'ResetPasswordView'
});

const router = useRouter();
const route = useRoute();

const token = ref('');
const email = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const error = ref('');
const isLoading = ref(false);
const isValidating = ref(true);
const isTokenValid = ref(false);
const expiresInMinutes = ref(0);
const showPassword = ref(false);
const showConfirmPassword = ref(false);

onMounted(async () => {
  token.value = route.query.token as string || '';

  if (!token.value) {
    error.value = 'Token de recuperación no encontrado en el enlace';
    isValidating.value = false;
    return;
  }

  // Validar token
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/auth/validate-reset-token/${token.value}`);

    if (response.ok) {
      const data = await response.json();
      email.value = data.email;
      expiresInMinutes.value = data.expires_in_minutes || 0;
      isTokenValid.value = true;
    } else {
      const errorData = await response.json();
      error.value = errorData.detail || 'El enlace de recuperación es inválido o ha expirado';
    }
  } catch (err) {
    console.error('Error al validar el token:', err);
    error.value = 'Error de conexión al validar el enlace';
  } finally {
    isValidating.value = false;
  }
});

const validatePassword = () => {
  if (!newPassword.value || !confirmPassword.value) {
    error.value = 'Por favor completa todos los campos';
    return false;
  }

  if (newPassword.value.length < 8) {
    error.value = 'La contraseña debe tener al menos 8 caracteres';
    return false;
  }

  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Las contraseñas no coinciden';
    return false;
  }

  // Validaciones adicionales de seguridad
  if (!/(?=.*[a-z])/.test(newPassword.value)) {
    error.value = 'La contraseña debe contener al menos una letra minúscula';
    return false;
  }

  if (!/(?=.*[A-Z])/.test(newPassword.value)) {
    error.value = 'La contraseña debe contener al menos una letra mayúscula';
    return false;
  }

  if (!/(?=.*\d)/.test(newPassword.value)) {
    error.value = 'La contraseña debe contener al menos un número';
    return false;
  }

  return true;
};

const getPasswordStrength = () => {
  const password = newPassword.value;
  if (!password) return { strength: 'none', text: '', color: '' };

  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/(?=.*[a-z])/.test(password)) score++;
  if (/(?=.*[A-Z])/.test(password)) score++;
  if (/(?=.*\d)/.test(password)) score++;
  if (/(?=.*[!@#$%^&*])/.test(password)) score++;

  if (score < 3) return { strength: 'weak', text: 'Débil', color: '#dc3545' };
  if (score < 5) return { strength: 'medium', text: 'Media', color: '#ffc107' };
  return { strength: 'strong', text: 'Fuerte', color: '#28a745' };
};

const handleSubmit = async () => {
  if (!validatePassword()) return;

  isLoading.value = true;
  error.value = '';

  try {
    const response = await fetch('http://127.0.0.1:8000/api/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: token.value,
        new_password: newPassword.value
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al restablecer la contraseña');
    }

    const data = await response.json();
    alert(`${data.message}\n\n🔐 Tu contraseña ha sido actualizada con éxito.`);
    router.push('/login');

  } catch (err: unknown) {
    if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = 'Error desconocido al actualizar la contraseña';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <AuthLayout title="Crear Nueva Contraseña">
    <div v-if="isValidating" class="text-gray-600 flex flex-col items-center gap-4 py-8">
      <i class="pi pi-spin pi-spinner text-4xl text-blue-600"></i>
      <p class="text-lg">Validando enlace de seguridad...</p>
    </div>

    <div v-else-if="!isTokenValid" class="text-center">
      <div class="mb-6 inline-flex items-center justify-center w-20 h-20 bg-danger-100 rounded-full">
        <i class="pi pi-times-circle text-4xl text-danger-600"></i>
      </div>
      <h3 class="text-gray-800 mb-3 font-bold text-2xl">Enlace No Válido</h3>
      <p class="text-gray-600 mb-8 text-lg leading-relaxed">{{ error }}</p>
      <div class="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-xl mb-8 text-left border border-orange-200">
        <p class="font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <i class="pi pi-info-circle text-orange-600"></i>
          Posibles causas
        </p>
        <ul class="m-0 ml-6 text-gray-700 space-y-2">
          <li>El enlace ha expirado (válido por 1 hora)</li>
          <li>Ya has usado este enlace anteriormente</li>
          <li>El enlace no es válido o está incompleto</li>
        </ul>
      </div>
      <div class="flex gap-3 justify-center flex-wrap">
        <router-link
          to="/forgot-password"
          class="inline-flex items-center gap-2 px-6 py-3.5 no-underline rounded-lg font-semibold transition-all duration-200 bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          <i class="pi pi-refresh"></i>
          Solicitar nuevo enlace
        </router-link>
        <router-link
          to="/login"
          class="inline-flex items-center gap-2 px-6 py-3.5 no-underline rounded-lg font-semibold transition-all duration-200 bg-gray-200 text-gray-700 hover:bg-gray-300 shadow-md hover:shadow-lg"
        >
          <i class="pi pi-sign-in"></i>
          Ir al login
        </router-link>
      </div>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="flex flex-col">
      <div class="flex items-start gap-4 bg-gradient-to-r from-blue-50 to-blue-100 px-5 py-4 rounded-xl mb-8 text-left border border-blue-200">
        <div class="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center mt-1">
          <i class="pi pi-user text-white text-lg"></i>
        </div>
        <div class="flex-1">
          <p class="m-0 mb-2 text-gray-800"><strong>Usuario:</strong> <span class="text-blue-700">{{ email }}</span></p>
          <p class="flex items-center gap-2 text-orange-600 text-sm m-0 font-medium">
            <i class="pi pi-clock"></i>
            Este enlace expira en <strong>{{ expiresInMinutes }} minutos</strong>
          </p>
        </div>
      </div>

      <div class="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-xl mb-8 text-left border border-purple-200">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
            <i class="pi pi-lock text-white text-lg"></i>
          </div>
          <div>
            <h3 class="m-0 mb-2 text-gray-800 font-semibold text-lg">Crear Nueva Contraseña</h3>
            <p class="m-0 text-gray-600 text-sm">Tu nueva contraseña debe ser segura y fácil de recordar para ti.</p>
          </div>
        </div>
      </div>

      <div v-if="error" class="bg-danger-50 text-danger-700 border border-danger-200 px-4 py-3 mb-4 rounded-lg flex items-center gap-2">
        <i class="pi pi-exclamation-triangle"></i>
        {{ error }}
      </div>

      <div class="mb-6 text-left">
        <label for="newPassword" class="flex items-center gap-2 mb-2 font-semibold text-gray-700">
          <i class="pi pi-key"></i>
          Nueva Contraseña
        </label>
        <div class="relative flex items-center">
          <input
            :type="showPassword ? 'text' : 'password'"
            id="newPassword"
            v-model="newPassword"
            required
            placeholder="Mínimo 8 caracteres"
            :disabled="isLoading"
            autocomplete="new-password"
            class="w-full pr-12 pl-4 py-3.5 border-2 border-gray-300 rounded-lg text-base transition-colors focus:outline-none focus:border-primary-500 disabled:bg-gray-100 disabled:opacity-70"
          >
          <button
            type="button"
            class="absolute right-3 bg-transparent border-none text-gray-500 cursor-pointer p-2 hover:text-primary-500"
            @click="showPassword = !showPassword"
            :disabled="isLoading"
          >
            <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
          </button>
        </div>

        <!-- Indicador de fortaleza de contraseña -->
        <div v-if="newPassword" class="mt-2 flex items-center gap-3">
          <div class="flex-grow h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              class="h-full transition-all duration-300"
              :style="{
                width: getPasswordStrength().strength === 'weak' ? '33%' :
                       getPasswordStrength().strength === 'medium' ? '66%' : '100%',
                backgroundColor: getPasswordStrength().color
              }"
            ></div>
          </div>
          <span class="text-sm font-medium" :style="{ color: getPasswordStrength().color }">
            Seguridad: {{ getPasswordStrength().text }}
          </span>
        </div>

        <div class="mt-3 px-3 py-2.5 bg-gray-100 rounded-md">
          <small class="text-gray-600">La contraseña debe contener:</small>
          <ul class="list-none p-0 m-0 mt-2">
            <li
              class="flex items-center gap-2 mb-1 transition-colors"
              :class="newPassword.length >= 8 ? 'text-success-500' : 'text-gray-500'"
            >
              <i class="text-xs" :class="newPassword.length >= 8 ? 'pi pi-check' : 'pi pi-times'"></i>
              Al menos 8 caracteres
            </li>
            <li
              class="flex items-center gap-2 mb-1 transition-colors"
              :class="/(?=.*[a-z])/.test(newPassword) ? 'text-success-500' : 'text-gray-500'"
            >
              <i class="text-xs" :class="/(?=.*[a-z])/.test(newPassword) ? 'pi pi-check' : 'pi pi-times'"></i>
              Una letra minúscula
            </li>
            <li
              class="flex items-center gap-2 mb-1 transition-colors"
              :class="/(?=.*[A-Z])/.test(newPassword) ? 'text-success-500' : 'text-gray-500'"
            >
              <i class="text-xs" :class="/(?=.*[A-Z])/.test(newPassword) ? 'pi pi-check' : 'pi pi-times'"></i>
              Una letra mayúscula
            </li>
            <li
              class="flex items-center gap-2 mb-1 transition-colors"
              :class="/(?=.*\d)/.test(newPassword) ? 'text-success-500' : 'text-gray-500'"
            >
              <i class="text-xs" :class="/(?=.*\d)/.test(newPassword) ? 'pi pi-check' : 'pi pi-times'"></i>
              Un número
            </li>
          </ul>
        </div>
      </div>

      <div class="mb-6 text-left">
        <label for="confirmPassword" class="flex items-center gap-2 mb-2 font-semibold text-gray-700">
          <i class="pi pi-check"></i>
          Confirmar Nueva Contraseña
        </label>
        <div class="relative flex items-center">
          <input
            :type="showConfirmPassword ? 'text' : 'password'"
            id="confirmPassword"
            v-model="confirmPassword"
            required
            placeholder="Repite tu nueva contraseña"
            :disabled="isLoading"
            autocomplete="new-password"
            class="w-full pr-12 pl-4 py-3.5 border-2 border-gray-300 rounded-lg text-base transition-colors focus:outline-none focus:border-primary-500 disabled:bg-gray-100 disabled:opacity-70"
          >
          <button
            type="button"
            class="absolute right-3 bg-transparent border-none text-gray-500 cursor-pointer p-2 hover:text-primary-500"
            @click="showConfirmPassword = !showConfirmPassword"
            :disabled="isLoading"
          >
            <i :class="showConfirmPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
          </button>
        </div>
        <div v-if="confirmPassword" class="mt-2 flex items-center gap-2 text-sm" :class="newPassword === confirmPassword ? 'text-success-500' : 'text-danger-500'">
          <i :class="newPassword === confirmPassword ? 'pi pi-check' : 'pi pi-times'"></i>
          <span>
            {{ newPassword === confirmPassword ? 'Las contraseñas coinciden' : 'Las contraseñas no coinciden' }}
          </span>
        </div>
      </div>

      <button
        type="submit"
        class="w-full px-6 py-4 bg-success-500 text-white border-none rounded-lg text-lg font-bold cursor-pointer transition-all mt-4 flex items-center justify-center gap-2 hover:bg-success-600 hover:-translate-y-0.5 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:transform-none"
        :disabled="isLoading"
      >
        <i v-if="isLoading" class="pi pi-spin pi-spinner"></i>
        <i v-else class="pi pi-save"></i>
        {{ isLoading ? 'Actualizando...' : 'Actualizar Contraseña' }}
      </button>

      <div class="flex items-center gap-2 mt-4 px-3 py-2.5 bg-blue-50 rounded-md text-blue-700">
        <i class="pi pi-info-circle"></i>
        <p class="m-0 text-sm">Después de cambiar tu contraseña, será necesario que inicies sesión nuevamente.</p>
      </div>

      <div class="mt-8">
        <router-link
          to="/login"
          class="text-gray-500 no-underline flex items-center justify-center gap-2 text-sm hover:text-primary-500 transition-colors"
        >
          <i class="pi pi-arrow-left"></i>
          Cancelar y volver al login
        </router-link>
      </div>
    </form>
  </AuthLayout>
</template>
