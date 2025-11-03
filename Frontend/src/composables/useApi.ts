import { ref } from 'vue';
import { API_BASE_URL } from '@/config/api';

/**
 * Composable para realizar peticiones a la API con autenticación
 */
export function useApi<T = unknown>() {
  const data = ref<T | null>(null);
  const error = ref<string | null>(null);
  const isLoading = ref(false);

  async function fetchData(endpoint: string, options: RequestInit = {}) {
    isLoading.value = true;
    error.value = null;

    const token = localStorage.getItem('userToken');

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
        } else if (response.status === 404) {
          throw new Error('Recurso no encontrado.');
        } else {
          throw new Error(`Error del servidor (${response.status})`);
        }
      }

      data.value = await response.json();
      return data.value;
    } catch (e) {
      console.error('Error en petición:', e);
      if (e instanceof Error) {
        error.value = e.message;
      } else {
        error.value = 'Error desconocido en la petición.';
      }
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  return { data, error, isLoading, fetchData };
}
