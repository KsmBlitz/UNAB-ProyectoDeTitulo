import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'primeicons/primeicons.css';
import './assets/styles.css'; // Tailwind CSS

import { authStore } from './auth/store';
import { jwtDecode } from 'jwt-decode';
import { API_BASE_URL } from './config/api';
import { themeStore } from './stores/themeStore';

const token = localStorage.getItem('userToken');
if (token) {
  try {
    const decodedToken: { sub: string; role: string } = jwtDecode(token);

  
    fetch(`${API_BASE_URL}/api/users/me`, {
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
themeStore.applyTheme();
