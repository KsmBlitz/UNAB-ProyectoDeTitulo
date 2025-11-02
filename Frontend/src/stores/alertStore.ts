// Frontend/src/stores/alertStore.ts
import { reactive, computed } from 'vue'
import { API_BASE_URL } from '@/config/api'

export interface AlertSummary {
  total: number
  critical: number
  warning: number
  info: number
  has_critical: boolean
  last_updated: string
}

export interface ActiveAlert {
  id: string
  type: string
  level: 'critical' | 'warning' | 'info'
  title: string
  message: string
  value?: number
  threshold_info: string
  location: string
  sensor_id?: string
  created_at: string
  is_resolved: boolean
}

export interface AlertsResponse {
  alerts: ActiveAlert[]
  count: number
  summary: {
    critical: number
    warning: number
    info: number
  }
  last_check: string
}

interface AlertStore {
  summary: AlertSummary
  activeAlerts: ActiveAlert[]
  isLoading: boolean
  error: string | null
  lastUpdated: Date | null
  pollingInterval: number | null
}

// Estado reactivo del store
const state = reactive<AlertStore>({
  summary: {
    total: 0,
    critical: 0,
    warning: 0,
    info: 0,
    has_critical: false,
    last_updated: new Date().toISOString()
  },
  activeAlerts: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  pollingInterval: null
})

/**
 * Retrieves authentication token from local storage
 */
function getAuthToken(): string | null {
  return localStorage.getItem('userToken')
}

/**
 * Makes authenticated API requests with error handling
 */
async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getAuthToken()
  if (!token) {
    throw new Error('No hay token de autenticación')
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...options.headers
  }

  // Crear un AbortController para manejar la cancelación manualmente
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 8000) // 8 segundos

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      if (response.status === 401) {
        // Token expirado o inválido
        localStorage.removeItem('userToken')
        window.location.href = '/login'
        throw new Error('Sesión expirada')
      }
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response
  } catch (error) {
    clearTimeout(timeoutId)

    // Manejo silencioso de errores de cancelación para evitar runtime.lastError
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        // No loggear errores de cancelación para evitar spam en consola
        throw new Error('Request cancelado')
      }
      if (error.message.includes('Failed to fetch')) {
        throw new Error('Error de conexión de red')
      }
    }
    throw error
  }
}

// Acciones del store
const actions = {
  // Obtener resumen de alertas con manejo silencioso de errores
  async fetchSummary(): Promise<void> {
    try {
      const response = await authenticatedFetch('/api/alerts/summary')
      const data: AlertSummary = await response.json()

      state.summary = data
      state.lastUpdated = new Date()
      state.error = null
    } catch (error) {
      // Solo actualizar error si no es de cancelación/timeout
      if (error instanceof Error && !error.message.includes('cancelado')) {
        state.error = error.message
      }
    }
  },

  // Obtener alertas activas completas con manejo mejorado
  async fetchActiveAlerts(): Promise<void> {
    try {
      state.isLoading = true
      const response = await authenticatedFetch('/api/alerts/active')

      const data: AlertsResponse = await response.json()

      state.activeAlerts = data.alerts || []
      state.summary = {
        total: data.count || 0,
        critical: data.summary?.critical || 0,
        warning: data.summary?.warning || 0,
        info: data.summary?.info || 0,
        has_critical: (data.summary?.critical || 0) > 0,
        last_updated: data.last_check || new Date().toISOString()
      }

      state.lastUpdated = new Date()
      state.error = null
    } catch (error) {
      // Solo mostrar errores significativos, no de cancelación
      if (error instanceof Error && !error.message.includes('cancelado')) {
        state.error = error.message
        // Solo limpiar alertas en errores reales, no timeouts
        if (!error.message.includes('conexión')) {
          state.activeAlerts = []
        }
      }
    } finally {
      state.isLoading = false
    }
  },

  // Cerrar/descartar una alerta
  async dismissAlert(alertId: string, reason?: string): Promise<boolean> {
    try {
      const response = await authenticatedFetch('/api/alerts/dismiss', {
        method: 'POST',
        body: JSON.stringify({
          alert_id: alertId,
          reason: reason
        })
      })

      if (response.ok) {
        // Actualizar tanto las alertas activas como el resumen
        await Promise.all([
          actions.fetchActiveAlerts(),
          actions.fetchSummary()
        ])
        return true
      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(`Error ${response.status}: ${errorData.detail || 'No se pudo cerrar la alerta'}`)
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error cerrando alerta'
      state.error = errorMessage
      throw error // Re-lanzar para que el componente pueda manejarlo
    }
  },

  // Iniciar polling automático cada 8 minutos para evitar solapamiento
  startPolling(): void {
    // Limpiar polling existente
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval)
    }

    // Fetch inicial después de un pequeño delay
    setTimeout(() => {
      actions.fetchSummary()
    }, 1000)

    // Configurar polling cada 8 minutos para evitar conflictos con backend
    state.pollingInterval = window.setInterval(() => {
      // Solo hacer fetch si no hay una request en progreso
      if (!state.isLoading) {
        actions.fetchSummary()
      }
    }, 480000) // 8 minutos = 480,000 ms
  },

  // Detener polling
  stopPolling(): void {
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval)
      state.pollingInterval = null
    }
  },

  /**
   * Forces immediate refresh of alert data
   */
  async refresh(): Promise<void> {
    await actions.fetchActiveAlerts()
  }
}

// Computadas
const getters = {
  // Alertas críticas solamente
  criticalAlerts: computed(() =>
    state.activeAlerts.filter(alert => alert.level === 'critical')
  ),

  // Alertas de advertencia
  warningAlerts: computed(() =>
    state.activeAlerts.filter(alert => alert.level === 'warning')
  ),

  // Indica si hay alertas críticas
  hasCriticalAlerts: computed(() =>
    state.summary.critical > 0
  ),

  // Indica si hay alguna alerta
  hasAnyAlerts: computed(() =>
    state.summary.total > 0
  ),

  // Estado de carga
  isLoading: computed(() => state.isLoading),

  // Error actual
  currentError: computed(() => state.error),

  // Última actualización formateada
  lastUpdateFormatted: computed(() => {
    if (!state.lastUpdated) return 'Nunca'

    const now = new Date()
    const diff = now.getTime() - state.lastUpdated.getTime()
    const minutes = Math.floor(diff / 60000)

    if (minutes === 0) return 'Hace un momento'
    if (minutes === 1) return 'Hace 1 minuto'
    if (minutes < 60) return `Hace ${minutes} minutos`

    const hours = Math.floor(minutes / 60)
    if (hours === 1) return 'Hace 1 hora'
    if (hours < 24) return `Hace ${hours} horas`

    return state.lastUpdated.toLocaleString()
  })
}

// Export del store - creado directamente como singleton
export const alertStore = {
  // Referencias directas al estado reactivo (NO spread)
  get summary() { return state.summary },
  get activeAlerts() { return state.activeAlerts },
  get isLoading() { return state.isLoading },
  get error() { return state.error },
  get lastUpdated() { return state.lastUpdated },
  get pollingInterval() { return state.pollingInterval },

  // Acciones
  ...actions,

  // Getters computadas
  ...getters,

  // Acceso directo al estado para debugging
  state
}

// AlertStore inicializado// Auto-limpiar polling cuando la página se cierra
window.addEventListener('beforeunload', () => {
  alertStore.stopPolling()
})
