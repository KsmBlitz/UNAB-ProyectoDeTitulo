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
  <!-- ✅ USAR EL NUEVO LAYOUT BASE -->
  <AuthLayout title="Crear Nueva Contraseña">
    <!-- Contenido existente sin el wrapper duplicado -->
    <div v-if="isValidating" class="validating-message">
      <i class="pi pi-spin pi-spinner"></i>
      <p>Validando enlace de seguridad...</p>
    </div>

    <div v-else-if="!isTokenValid" class="error-state">
      <i class="pi pi-times-circle" style="font-size: 4rem; color: #dc3545; margin-bottom: 1rem;"></i>
      <h3>❌ Enlace No Válido</h3>
      <p>{{ error }}</p>
      <div class="help-text">
        <p><strong>Posibles causas:</strong></p>
        <ul>
          <li>El enlace ha expirado (válido por 1 hora)</li>
          <li>Ya has usado este enlace</li>
          <li>El enlace no es válido</li>
        </ul>
      </div>
      <div class="action-buttons">
        <router-link to="/forgot-password" class="retry-link">
          <i class="pi pi-refresh"></i>
          Solicitar nuevo enlace
        </router-link>
        <router-link to="/login" class="login-link">
          <i class="pi pi-sign-in"></i>
          Ir al login
        </router-link>
      </div>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="reset-password-form">
      <div class="user-info">
        <i class="pi pi-user"></i>
        <div>
          <p><strong>Usuario:</strong> {{ email }}</p>
          <p class="expires-info">
            <i class="pi pi-clock"></i>
            Este enlace expira en {{ expiresInMinutes }} minutos
          </p>
        </div>
      </div>

      <div class="instruction">
        <h3>🔐 Crear Nueva Contraseña</h3>
        <p>Tu nueva contraseña debe ser segura y fácil de recordar para ti.</p>
      </div>

      <div v-if="error" class="error-message">
        <i class="pi pi-exclamation-triangle"></i>
        {{ error }}
      </div>

      <div class="form-group">
        <label for="newPassword">
          <i class="pi pi-key"></i>
          Nueva Contraseña
        </label>
        <div class="password-input-container">
          <input
            :type="showPassword ? 'text' : 'password'"
            id="newPassword"
            v-model="newPassword"
            required
            placeholder="Mínimo 8 caracteres"
            :disabled="isLoading"
            autocomplete="new-password"
          >
          <button
            type="button"
            class="toggle-password"
            @click="showPassword = !showPassword"
            :disabled="isLoading"
          >
            <i :class="showPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
          </button>
        </div>

        <!-- Indicador de fortaleza de contraseña -->
        <div v-if="newPassword" class="password-strength">
          <div class="strength-bar">
            <div
              class="strength-fill"
              :style="{
                width: getPasswordStrength().strength === 'weak' ? '33%' :
                       getPasswordStrength().strength === 'medium' ? '66%' : '100%',
                backgroundColor: getPasswordStrength().color
              }"
            ></div>
          </div>
          <span :style="{ color: getPasswordStrength().color }">
            Seguridad: {{ getPasswordStrength().text }}
          </span>
        </div>

        <div class="password-requirements">
          <small>La contraseña debe contener:</small>
          <ul>
            <li :class="{ valid: newPassword.length >= 8 }">
              <i :class="newPassword.length >= 8 ? 'pi pi-check' : 'pi pi-times'"></i>
              Al menos 8 caracteres
            </li>
            <li :class="{ valid: /(?=.*[a-z])/.test(newPassword) }">
              <i :class="/(?=.*[a-z])/.test(newPassword) ? 'pi pi-check' : 'pi pi-times'"></i>
              Una letra minúscula
            </li>
            <li :class="{ valid: /(?=.*[A-Z])/.test(newPassword) }">
              <i :class="/(?=.*[A-Z])/.test(newPassword) ? 'pi pi-check' : 'pi pi-times'"></i>
              Una letra mayúscula
            </li>
            <li :class="{ valid: /(?=.*\d)/.test(newPassword) }">
              <i :class="/(?=.*\d)/.test(newPassword) ? 'pi pi-check' : 'pi pi-times'"></i>
              Un número
            </li>
          </ul>
        </div>
      </div>

      <div class="form-group">
        <label for="confirmPassword">
          <i class="pi pi-check"></i>
          Confirmar Nueva Contraseña
        </label>
        <div class="password-input-container">
          <input
            :type="showConfirmPassword ? 'text' : 'password'"
            id="confirmPassword"
            v-model="confirmPassword"
            required
            placeholder="Repite tu nueva contraseña"
            :disabled="isLoading"
            autocomplete="new-password"
          >
          <button
            type="button"
            class="toggle-password"
            @click="showConfirmPassword = !showConfirmPassword"
            :disabled="isLoading"
          >
            <i :class="showConfirmPassword ? 'pi pi-eye-slash' : 'pi pi-eye'"></i>
          </button>
        </div>
        <div v-if="confirmPassword" class="password-match">
          <i :class="newPassword === confirmPassword ? 'pi pi-check' : 'pi pi-times'"></i>
          <span :class="{ valid: newPassword === confirmPassword }">
            {{ newPassword === confirmPassword ? 'Las contraseñas coinciden' : 'Las contraseñas no coinciden' }}
          </span>
        </div>
      </div>

      <button type="submit" class="submit-button" :disabled="isLoading">
        <i v-if="isLoading" class="pi pi-spin pi-spinner"></i>
        <i v-else class="pi pi-save"></i>
        {{ isLoading ? 'Actualizando...' : 'Actualizar Contraseña' }}
      </button>

      <div class="security-info">
        <i class="pi pi-info-circle"></i>
        <p>Después de cambiar tu contraseña, será necesario que inicies sesión nuevamente.</p>
      </div>

      <div class="form-footer">
        <router-link to="/login" class="back-link">
          <i class="pi pi-arrow-left"></i>
          Cancelar y volver al login
        </router-link>
      </div>
    </form>
  </AuthLayout>
</template>

<style scoped>
.reset-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f4f6f9;
  padding: 1rem;
}

.reset-password-card {
  background-color: #fff;
  padding: 2.5rem 3rem;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.logo {
  margin-bottom: 2rem;
}

.logo h2 {
  margin: 0.5rem 0 0;
  color: #2c3e50;
}

.validating-message {
  color: #6c757d;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.error-state {
  text-align: center;
}

.error-state h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.help-text {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  margin: 1.5rem 0;
  text-align: left;
}

.help-text ul {
  margin: 0.5rem 0 0 1rem;
  color: #6c757d;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.retry-link, .login-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s;
}

.retry-link {
  background-color: #3498db;
  color: white;
}

.retry-link:hover {
  background-color: #2980b9;
}

.login-link {
  background-color: #6c757d;
  color: white;
}

.login-link:hover {
  background-color: #5a6268;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  background-color: #e3f2fd;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  text-align: left;
}

.user-info i {
  font-size: 1.5rem;
  color: #1976d2;
}

.expires-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #f57c00;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.instruction {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  text-align: left;
}

.instruction h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.instruction p {
  margin: 0;
  color: #6c757d;
}

.reset-password-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 1.5rem;
  text-align: left;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #34495e;
}

.password-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 3rem 0.875rem 1rem;
  border: 2px solid #ced4da;
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.form-group input:disabled {
  background-color: #f8f9fa;
  opacity: 0.7;
}

.toggle-password {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 0.5rem;
}

.toggle-password:hover {
  color: #3498db;
}

.password-strength {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.strength-bar {
  flex-grow: 1;
  height: 4px;
  background-color: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
}

.password-requirements {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
}

.password-requirements li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  color: #6c757d;
  transition: color 0.2s;
}

.password-requirements li.valid {
  color: #28a745;
}

.password-requirements li i {
  font-size: 0.8rem;
}

.password-match {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #dc3545;
}

.password-match.valid,
.password-match .valid {
  color: #28a745;
}

.submit-button {
  width: 100%;
  padding: 1rem 1.5rem;
  background-color: #28a745;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.submit-button:hover:not(:disabled) {
  background-color: #218838;
  transform: translateY(-2px);
}

.submit-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  transform: none;
}

.security-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #e3f2fd;
  border-radius: 6px;
  color: #1565c0;
}

.form-footer {
  margin-top: 2rem;
}

.back-link {
  color: #6c757d;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.back-link:hover {
  color: #3498db;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
