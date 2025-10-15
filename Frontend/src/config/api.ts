// Frontend/src/config/api.ts
const getApiBaseUrl = () => {
  // Usar localhost para desarrollo local
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';  // ✅ LOCALHOST PARA DESARROLLO
  }
  // En producción, usar la URL de producción
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();
