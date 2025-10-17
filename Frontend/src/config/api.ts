// Frontend/src/config/api.ts
const getApiBaseUrl = () => {
  // En desarrollo local
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }

  // En producción con Docker
  // Docker Compose expondrá el backend en el puerto 8000
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();
