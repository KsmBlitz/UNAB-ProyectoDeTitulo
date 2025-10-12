import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'primeicons/primeicons.css';

import { authStore } from './auth/store';
import { jwtDecode } from 'jwt-decode';

const token = localStorage.getItem('userToken');
if (token) {
  try {
    const decodedToken: { sub: string; role: string } = jwtDecode(token);

    // Hacer una petición para obtener los datos completos del usuario
    fetch('http://127.0.0.1:8000/api/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => {
      if (response.ok) {
        return response.json();
      }
      throw new Error('No se pudieron obtener los datos del usuario');
    })
    .then(userData => {
      authStore.user = {
        email: userData.email,
        role: userData.role,
        full_name: userData.full_name
      };
    })
    .catch(error => {
      console.error("Error obteniendo datos del usuario:", error);
      // Fallback con datos básicos del token
      authStore.user = {
        email: decodedToken.sub,
        role: decodedToken.role
      };
    });
  } catch (error) {
    console.error("Token inválido encontrado en localStorage", error);
    localStorage.removeItem('userToken');
  }
}

const app = createApp(App)
app.use(router)
app.mount('#app')
