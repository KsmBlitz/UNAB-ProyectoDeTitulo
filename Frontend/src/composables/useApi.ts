import { ref } from 'vue';
import { API_BASE_URL } from '@/config/api';

/**
 * Composable para realizar peticiones a la API con autenticación
 */
export function useApi<T = unknown>() {
  const data = ref<T | null>(null);
  const error = ref<string | null>(null);
  const isLoading = ref(false);

  async function fetchData(endpoint: string, options: RequestInit = {}, responseType: 'json' | 'blob' = 'json') {
    isLoading.value = true;
    error.value = null;

    const token = localStorage.getItem('userToken');

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          ...(responseType === 'json' && { 'Content-Type': 'application/json' }),
          ...options.headers,
        },
      });

      if (!response.ok) {
        // Intentar obtener el mensaje de error del backend
        let errorMessage = `Error del servidor (${response.status})`;
        
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // Si no se puede parsear el JSON, usar el mensaje genérico
        }
        
        if (response.status === 401) {
          throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
        } else if (response.status === 404) {
          throw new Error('Recurso no encontrado.');
        } else {
          throw new Error(errorMessage);
        }
      }

      if (responseType === 'blob') {
        data.value = await response.blob() as T;
      } else {
        data.value = await response.json();
      }
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

  async function get(endpoint: string, options: { params?: Record<string, any>, responseType?: 'json' | 'blob' } = {}) {
    const { params, responseType = 'json', ...restOptions } = options;
    let url = endpoint;
    
    if (params) {
      const queryString = new URLSearchParams(params).toString();
      url = `${endpoint}?${queryString}`;
    }
    
    return fetchData(url, {
      method: 'GET',
      ...restOptions as RequestInit
    }, responseType);
  }

  async function post(endpoint: string, body: any, options: RequestInit = {}) {
    return fetchData(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
      ...options
    });
  }

  return { data, error, isLoading, fetchData, get, post };
}
