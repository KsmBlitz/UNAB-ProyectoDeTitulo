// Frontend/src/config/api.ts
const getApiBaseUrl = () => {
  // En desarrollo local
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }

  // En producción: usar rutas relativas al origen actual.
  // Dejar la URL relativa evita problemas cuando la app se sirve desde
  // distintos puertos (dev server vs proxy nginx) y permite que
  // fetch('/api/...') use el mismo host/puerto que la aplicación.
  return ''
};

export const API_BASE_URL = getApiBaseUrl();
