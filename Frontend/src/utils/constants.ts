/**
 * Constantes de la aplicación
 */

export const APP_NAME = 'AquaStat';
export const APP_VERSION = '1.0.0';

// Roles de usuario
export const USER_ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  OPERATOR: 'operator',
} as const;

export type UserRole = typeof USER_ROLES[keyof typeof USER_ROLES];

// Tipos de sensores
export const SENSOR_TYPES = {
  PH: 'ph',
  TEMPERATURE: 'temperature',
  CONDUCTIVITY: 'conductivity',
  WATER_LEVEL: 'water_level',
} as const;

// Estados de sensores
export const SENSOR_STATUS = {
  ONLINE: 'online',
  OFFLINE: 'offline',
  WARNING: 'warning',
} as const;

// Íconos por tipo de métrica
export const METRIC_ICONS = {
  ph: 'pi pi-flask',
  temperature: 'pi pi-sun',
  conductivity: 'pi pi-bolt',
  water_level: 'pi pi-chart-bar',
  default: 'pi pi-circle',
} as const;

// Intervalos de actualización (en milisegundos)
export const REFRESH_INTERVALS = {
  FAST: 5000,    // 5 segundos
  NORMAL: 30000, // 30 segundos
  SLOW: 60000,   // 1 minuto
} as const;

// Límites de paginación
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

// Mensajes de error comunes
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Error de conexión. Verifica tu conexión a internet.',
  UNAUTHORIZED: 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.',
  NOT_FOUND: 'El recurso solicitado no fue encontrado.',
  SERVER_ERROR: 'Error del servidor. Intenta nuevamente más tarde.',
  VALIDATION_ERROR: 'Por favor, verifica los datos ingresados.',
} as const;

// Mensajes de éxito comunes
export const SUCCESS_MESSAGES = {
  SAVE_SUCCESS: 'Cambios guardados exitosamente.',
  DELETE_SUCCESS: 'Elemento eliminado exitosamente.',
  CREATE_SUCCESS: 'Elemento creado exitosamente.',
  UPDATE_SUCCESS: 'Elemento actualizado exitosamente.',
} as const;

// Rutas de la aplicación
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  USERS: '/users',
  ALERTS: '/alerts',
  SETTINGS: '/settings',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
} as const;
