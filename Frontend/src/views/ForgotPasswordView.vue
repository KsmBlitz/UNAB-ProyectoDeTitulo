<script setup lang="ts">
import { ref } from 'vue';
import { RouterLink } from 'vue-router';

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
  <div class="forgot-password-container">
    <div class="forgot-password-card">
      <div class="logo">
        <i class="pi pi-shield" style="font-size: 3rem; color: #3498db;"></i>
        <h2>Recuperar Contraseña</h2>
      </div>

      <div v-if="isSuccess" class="success-message">
        <i class="pi pi-check-circle"></i>
        <h3>📧 Solicitud Enviada</h3>
        <p>{{ message }}</p>

        <div class="instructions">
          <h4>📋 Próximos pasos:</h4>
          <ol>
            <li>Revisa tu bandeja de entrada en <strong>{{ email }}</strong></li>
            <li>Si no encuentras el email, revisa tu carpeta de spam</li>
            <li>Haz clic en el enlace del email para cambiar tu contraseña</li>
            <li>El enlace expirará en 1 hora por seguridad</li>
          </ol>
        </div>

        <div class="dev-info">
          <strong>💻 Modo desarrollo:</strong> Si los emails no están configurados, revisa la consola del servidor backend para obtener el enlace directo.
        </div>

        <div class="action-buttons">
          <RouterLink to="/login" class="back-to-login">
            <i class="pi pi-arrow-left"></i>
            Volver al inicio de sesión
          </RouterLink>
          <button @click="isSuccess = false; email = ''; message = ''" class="try-again-btn">
            <i class="pi pi-refresh"></i>
            Intentar con otro email
          </button>
        </div>
      </div>

      <form v-else @submit.prevent="handleSubmit" class="forgot-password-form">
        <div class="instruction-box">
          <h3>🔐 ¿Olvidaste tu contraseña?</h3>
          <p>No te preocupes. Ingresa tu correo electrónico y te enviaremos un enlace seguro para crear una nueva contraseña.</p>
        </div>

        <div v-if="error" class="error-message">
          <i class="pi pi-exclamation-triangle"></i>
          {{ error }}
        </div>

        <div class="form-group">
          <label for="email">
            <i class="pi pi-envelope"></i>
            Correo Electrónico
          </label>
          <input
            type="email"
            id="email"
            v-model="email"
            required
            placeholder="tu@ejemplo.com"
            :disabled="isLoading"
            autocomplete="email"
          >
        </div>

        <button type="submit" class="submit-button" :disabled="isLoading || !email.trim()">
          <i v-if="isLoading" class="pi pi-spin pi-spinner"></i>
          <i v-else class="pi pi-send"></i>
          {{ isLoading ? 'Enviando...' : 'Enviar Enlace de Recuperación' }}
        </button>

        <div class="security-note">
          <i class="pi pi-info-circle"></i>
          <small>Por seguridad, el enlace expirará en 1 hora y solo funcionará una vez.</small>
        </div>

        <div class="form-footer">
          <RouterLink to="/login" class="back-link">
            <i class="pi pi-arrow-left"></i>
            Volver al inicio de sesión
          </RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f4f6f9;
  padding: 1rem;
}

.forgot-password-card {
  background-color: #fff;
  padding: 2.5rem 3rem;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 480px;
  text-align: center;
}

.logo {
  margin-bottom: 2rem;
}

.logo h2 {
  margin: 0.5rem 0 0;
  color: #2c3e50;
}

.instruction-box {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  text-align: left;
}

.instruction-box h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.instruction-box p {
  margin: 0;
  color: #6c757d;
  line-height: 1.5;
}

.forgot-password-form {
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

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
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

.submit-button {
  width: 100%;
  padding: 1rem 1.5rem;
  background-color: #3498db;
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
  background-color: #2980b9;
  transform: translateY(-2px);
}

.submit-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  transform: none;
}

.security-note {
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

.success-message {
  text-align: center;
  color: #28a745;
}

.success-message i {
  font-size: 4rem;
  margin-bottom: 1rem;
  display: block;
}

.success-message h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.success-message p {
  margin-bottom: 2rem;
  color: #6c757d;
  line-height: 1.5;
}

.instructions {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  text-align: left;
}

.instructions h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.instructions ol {
  margin: 0;
  padding-left: 1.5rem;
}

.instructions li {
  margin-bottom: 0.5rem;
  color: #495057;
}

.dev-info {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  margin-bottom: 2rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.back-to-login, .try-again-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 600;
  transition: all 0.2s;
}

.back-to-login {
  background-color: #28a745;
  color: white;
}

.back-to-login:hover {
  background-color: #218838;
}

.try-again-btn {
  background-color: #6c757d;
  color: white;
  border: none;
  cursor: pointer;
}

.try-again-btn:hover {
  background-color: #5a6268;
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
