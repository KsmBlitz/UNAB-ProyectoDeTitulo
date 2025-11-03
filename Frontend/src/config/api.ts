// Frontend/src/config/api.ts
const getApiBaseUrl = () => {
  // En desarrollo local
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }

  // En producción: usar el mismo host que sirvió el frontend.
  // `localhost` en el navegador apunta a la máquina del cliente y provoca errores
  // cuando el frontend está en un servidor remoto (como EC2). Construimos la
  // URL usando el hostname actual para apuntar al backend en el mismo host.
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${host}:8000`;
};

export const API_BASE_URL = getApiBaseUrl();
