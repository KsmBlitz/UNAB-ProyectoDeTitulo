// Frontend/src/config/api.ts
const getApiBaseUrl = () => {
  // En desarrollo local
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }

  // En producción: usar el proxy inverso en el mismo host
  // El proxy Nginx redirige /api al backend
  const protocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';
  const host = typeof window !== 'undefined' ? window.location.host : 'localhost';
  return `${protocol}//${host}`;
};

export const API_BASE_URL = getApiBaseUrl();
