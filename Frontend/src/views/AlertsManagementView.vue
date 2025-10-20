<template>
  <div class="alerts-management">
    <!-- Header de la vista -->
    <div class="alerts-header">
      <div class="header-left">
        <h1 class="page-title">
          <i class="pi pi-exclamation-triangle"></i>
          Gestión de Alertas del Sistema
        </h1>
        <p class="page-description">
          Monitoreo en tiempo real de condiciones críticas para el cultivo de arándanos
        </p>
      </div>

      <div class="header-actions">
        <button
          @click="refreshAlerts"
          class="action-btn refresh-btn"
          :disabled="isLoading"
          title="Actualizar alertas"
        >
          <i class="pi pi-refresh" :class="{ 'pi-spin': isLoading }"></i>
          Actualizar
        </button>

        <button
          v-if="isAdmin"
          @click="openConfigModal"
          class="action-btn config-btn"
          title="Configurar umbrales de alertas"
        >
          <i class="pi pi-cog"></i>
          Configurar Umbrales
        </button>


      </div>
    </div>

    <!-- Resumen de alertas -->
    <div class="alerts-summary">
      <div class="summary-card critical" v-if="alertStore.summary.critical > 0">
        <div class="card-icon">
          <i class="pi pi-exclamation-triangle"></i>
        </div>
        <div class="card-content">
          <div class="card-number">{{ alertStore.summary.critical }}</div>
          <div class="card-label">Alertas Críticas</div>
        </div>
      </div>

      <div class="summary-card warning" v-if="alertStore.summary.warning > 0">
        <div class="card-icon">
          <i class="pi pi-exclamation-circle"></i>
        </div>
        <div class="card-content">
          <div class="card-number">{{ alertStore.summary.warning }}</div>
          <div class="card-label">Advertencias</div>
        </div>
      </div>

      <div class="summary-card info" v-if="alertStore.summary.info > 0">
        <div class="card-icon">
          <i class="pi pi-info-circle"></i>
        </div>
        <div class="card-content">
          <div class="card-number">{{ alertStore.summary.info }}</div>
          <div class="card-label">Informativas</div>
        </div>
      </div>

      <div class="summary-card success" v-if="!alertStore.hasAnyAlerts">
        <div class="card-icon">
          <i class="pi pi-check-circle"></i>
        </div>
        <div class="card-content">
          <div class="card-number">0</div>
          <div class="card-label">Todo Normal</div>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filters-section">
      <div class="filters-row">
        <div class="filter-group">
          <label>Nivel de Alerta:</label>
          <select v-model="filters.level" @change="applyFilters">
            <option value="">Todos los niveles</option>
            <option value="critical">Críticas</option>
            <option value="warning">Advertencias</option>
            <option value="info">Informativas</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Tipo de Alerta:</label>
          <select v-model="filters.type" @change="applyFilters">
            <option value="">Todos los tipos</option>
            <option value="ph_range">pH fuera de rango</option>
            <option value="conductivity">Conductividad elevada</option>
            <option value="temperature">Temperatura anormal</option>
            <option value="sensor_disconnection">Sensor desconectado</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Período:</label>
          <select v-model="filters.period" @change="applyFilters">
            <option value="today">Hoy</option>
            <option value="week">Esta semana</option>
            <option value="month">Este mes</option>
            <option value="all">Todo el historial</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Lista de alertas activas -->
    <div class="alerts-content">
      <div class="section-header">
        <h2>
          <i class="pi pi-bell"></i>
          Alertas Activas ({{ filteredActiveAlerts.length }})
        </h2>
        <div class="last-update">
          Última actualización: {{ alertStore.lastUpdateFormatted }}
        </div>
      </div>

      <!-- Estado de carga o vacío -->
      <div v-if="isLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i>
        <span>Cargando alertas...</span>
      </div>

      <div v-else-if="filteredActiveAlerts.length === 0" class="empty-state">
        <i class="pi pi-check-circle"></i>
        <h3>No hay alertas activas</h3>
        <p>Todas las condiciones están dentro de los rangos normales para el cultivo de arándanos.</p>
      </div>

      <!-- Lista de alertas -->
      <div v-else class="alerts-list">
        <div
          v-for="alert in filteredActiveAlerts"
          :key="alert.id"
          class="alert-item"
          :class="`alert-${alert.level}`"
        >
          <div class="alert-main">
            <div class="alert-icon">
              <i :class="getAlertIcon(alert.level)"></i>
            </div>

            <div class="alert-info">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-message">{{ alert.message }}</div>
              <div class="alert-details">
                <span class="detail-item">
                  <i class="pi pi-map-marker"></i>
                  {{ alert.location }}
                </span>
                <span class="detail-item" v-if="alert.sensor_id">
                  <i class="pi pi-microchip"></i>
                  Sensor: {{ alert.sensor_id }}
                </span>
                <span class="detail-item">
                  <i class="pi pi-clock"></i>
                  {{ formatAlertTime(alert.created_at) }}
                </span>
              </div>
              <div class="alert-threshold">
                <i class="pi pi-info-circle"></i>
                {{ alert.threshold_info }}
              </div>
            </div>
          </div>

          <div class="alert-actions">
            <button
              @click="dismissAlert(alert)"
              class="action-btn dismiss-btn"
              :disabled="dismissingAlerts.has(alert.id)"
            >
              <i class="pi pi-times" v-if="!dismissingAlerts.has(alert.id)"></i>
              <i class="pi pi-spin pi-spinner" v-else></i>
              {{ dismissingAlerts.has(alert.id) ? 'Cerrando...' : 'Cerrar Alerta' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Historial de alertas (solo para admin) -->
    <div v-if="isAdmin" class="history-section">
      <div class="section-header">
        <h2>
          <i class="pi pi-history"></i>
          Historial de Alertas
        </h2>
        <div class="header-actions">
          <button
            @click="loadHistory"
            class="action-btn secondary-btn"
            :disabled="loadingHistory"
          >
            <i class="pi pi-refresh" :class="{ 'pi-spin': loadingHistory }"></i>
            Refrescar Historial
          </button>

          <button
            @click="clearHistory"
            class="action-btn danger-btn"
            :disabled="clearingHistory || alertHistory.length === 0"
            title="Borrar todo el historial (solo admin)"
          >
            <i class="pi pi-trash" :class="{ 'pi-spin': clearingHistory }"></i>
            {{ clearingHistory ? 'Borrando...' : 'Borrar Historial' }}
          </button>
        </div>
      </div>

      <div v-if="alertHistory.length > 0" class="history-table">
        <table>
          <thead>
            <tr>
              <th>Fecha/Hora</th>
              <th>Tipo</th>
              <th>Nivel</th>
              <th>Mensaje</th>
              <th>Duración</th>
              <th>Cerrada por</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="historyItem in alertHistory" :key="historyItem.id">
              <td>{{ formatHistoryDate(historyItem.created_at) }}</td>
              <td>{{ getTypeLabel(historyItem.type) }}</td>
              <td>
                <span class="level-badge" :class="`level-${historyItem.level}`">
                  {{ getLevelLabel(historyItem.level) }}
                </span>
              </td>
              <td>{{ historyItem.message }}</td>
              <td>{{ historyItem.duration_minutes || 0 }} min</td>
              <td>{{ historyItem.dismissed_by || 'Auto-resuelta' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal de configuración de umbrales (solo admin) -->
    <div v-if="showConfigModal && isAdmin" class="modal-overlay" @click="showConfigModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Configuración de Umbrales para Arándanos</h3>
          <button @click="showConfigModal = false" class="modal-close">
            <i class="pi pi-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div v-if="loadingConfig" class="loading-state">
            <i class="pi pi-spin pi-spinner"></i>
            <span>Cargando configuración...</span>
          </div>

          <form v-else @submit.prevent="saveThresholdConfig" class="threshold-form">
            <!-- Mensaje de estado -->
            <div v-if="configMessage" class="config-message" :class="{ success: configMessage.includes('exitosamente'), error: !configMessage.includes('exitosamente') }">
              {{ configMessage }}
            </div>

            <!-- Configuración de pH -->
            <div class="form-section">
              <h4><i class="pi pi-chart-bar"></i> Niveles de pH</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="ph_min">pH Mínimo:</label>
                  <input
                    id="ph_min"
                    v-model.number="thresholdConfig.ph_min"
                    type="number"
                    step="0.1"
                    min="0"
                    max="14"
                    :class="{ error: configErrors.ph_min }"
                  >
                  <span v-if="configErrors.ph_min" class="error-text">{{ configErrors.ph_min }}</span>
                </div>
                <div class="form-group">
                  <label for="ph_max">pH Máximo:</label>
                  <input
                    id="ph_max"
                    v-model.number="thresholdConfig.ph_max"
                    type="number"
                    step="0.1"
                    min="0"
                    max="14"
                    :class="{ error: configErrors.ph_max }"
                  >
                  <span v-if="configErrors.ph_max" class="error-text">{{ configErrors.ph_max }}</span>
                </div>
              </div>
            </div>

            <!-- Configuración de Conductividad -->
            <div class="form-section">
              <h4><i class="pi pi-bolt"></i> Conductividad Eléctrica</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="conductivity_max">Conductividad Máxima (dS/m):</label>
                  <input
                    id="conductivity_max"
                    v-model.number="thresholdConfig.conductivity_max"
                    type="number"
                    step="0.1"
                    min="0"
                    :class="{ error: configErrors.conductivity_max }"
                  >
                  <span v-if="configErrors.conductivity_max" class="error-text">{{ configErrors.conductivity_max }}</span>
                </div>
              </div>
            </div>

            <!-- Configuración de Nivel de Agua -->
            <div class="form-section">
              <h4><i class="pi pi-tint"></i> Nivel de Agua</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="water_level_min">Nivel Mínimo (%):</label>
                  <input
                    id="water_level_min"
                    v-model.number="thresholdConfig.water_level_min"
                    type="number"
                    min="0"
                    max="100"
                    :class="{ error: configErrors.water_level_min }"
                  >
                  <span v-if="configErrors.water_level_min" class="error-text">{{ configErrors.water_level_min }}</span>
                </div>
                <div class="form-group">
                  <label for="water_level_max">Nivel Máximo (%):</label>
                  <input
                    id="water_level_max"
                    v-model.number="thresholdConfig.water_level_max"
                    type="number"
                    min="0"
                    max="100"
                    :class="{ error: configErrors.water_level_max }"
                  >
                  <span v-if="configErrors.water_level_max" class="error-text">{{ configErrors.water_level_max }}</span>
                </div>
              </div>
            </div>

            <!-- Configuración de Temperatura -->
            <div class="form-section">
              <h4><i class="pi pi-sun"></i> Temperatura</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="temperature_min">Temperatura Mínima (°C):</label>
                  <input
                    id="temperature_min"
                    v-model.number="thresholdConfig.temperature_min"
                    type="number"
                    step="0.1"
                    :class="{ error: configErrors.temperature_min }"
                  >
                  <span v-if="configErrors.temperature_min" class="error-text">{{ configErrors.temperature_min }}</span>
                </div>
                <div class="form-group">
                  <label for="temperature_max">Temperatura Máxima (°C):</label>
                  <input
                    id="temperature_max"
                    v-model.number="thresholdConfig.temperature_max"
                    type="number"
                    step="0.1"
                    :class="{ error: configErrors.temperature_max }"
                  >
                  <span v-if="configErrors.temperature_max" class="error-text">{{ configErrors.temperature_max }}</span>
                </div>
              </div>
            </div>
          </form>
        </div>

        <div class="modal-footer">
          <button @click="showConfigModal = false" class="action-btn secondary-btn" :disabled="savingConfig">
            Cancelar
          </button>
          <button @click="saveThresholdConfig" class="action-btn primary-btn" :disabled="loadingConfig || savingConfig">
            <i v-if="savingConfig" class="pi pi-spin pi-spinner"></i>
            {{ savingConfig ? 'Guardando...' : 'Guardar Cambios' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { alertStore, type ActiveAlert } from '@/stores/alertStore'
import { authStore } from '@/auth/store'
import { API_BASE_URL } from '@/config/api'

defineOptions({
  name: 'AlertsManagementView'
})

// Tipos para el historial
interface AlertHistoryItem {
  id: string
  type: string
  level: 'critical' | 'warning' | 'info'
  message: string
  created_at: string
  resolved_at?: string
  duration_minutes?: number
  dismissed_by?: string
}

// Tipo para los datos del API de historial
interface AlertHistoryApiItem {
  _id?: string
  alert_id: string
  type: string
  level: 'critical' | 'warning' | 'info'
  message: string
  created_at: string
  dismissed_at?: string
  duration_minutes?: string | number
  dismissed_by?: string
}

// Estado local
const isLoading = ref(false)
const loadingHistory = ref(false)
const clearingHistory = ref(false)
const showConfigModal = ref(false)
const loadingConfig = ref(false)
const savingConfig = ref(false)
const dismissingAlerts = ref(new Set<string>())
const alertHistory = ref<AlertHistoryItem[]>([])

// Configuración de umbrales
const thresholdConfig = ref({
  ph_min: 4.5,
  ph_max: 6.5,
  conductivity_max: 1.5,
  water_level_min: 20,
  water_level_max: 85,
  temperature_min: 5,
  temperature_max: 35
})

const configErrors = ref<Record<string, string>>({})
const configMessage = ref('')

// Filtros
const filters = ref({
  level: '',
  type: '',
  period: 'all'
})

// Computadas
const isAdmin = computed(() => authStore.user?.role === 'admin')

const filteredActiveAlerts = computed(() => {
  let alerts = alertStore.activeAlerts

  if (filters.value.level) {
    alerts = alerts.filter(alert => alert.level === filters.value.level)
  }

  if (filters.value.type) {
    alerts = alerts.filter(alert => alert.type === filters.value.type)
  }

  // Ordenar por nivel de prioridad y fecha
  return alerts.sort((a, b) => {
    const priorityOrder = { critical: 3, warning: 2, info: 1 }
    const aPriority = priorityOrder[a.level as keyof typeof priorityOrder] || 0
    const bPriority = priorityOrder[b.level as keyof typeof priorityOrder] || 0

    if (aPriority !== bPriority) {
      return bPriority - aPriority // Mayor prioridad primero
    }

    // Si mismo nivel, más reciente primero
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

// Funciones
function getAlertIcon(level: string): string {
  switch (level) {
    case 'critical':
      return 'pi pi-exclamation-triangle'
    case 'warning':
      return 'pi pi-exclamation-circle'
    case 'info':
      return 'pi pi-info-circle'
    default:
      return 'pi pi-bell'
  }
}

function formatAlertTime(dateString: string): string {
  try {
    const date = new Date(dateString)

    // Obtener hora actual en zona horaria de Chile
    const nowInChile = new Date().toLocaleString('sv-SE', { timeZone: 'America/Santiago' })
    const now = new Date(nowInChile)

    const diffMs = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diffMs / 60000)

    if (diffMinutes === 0) return 'Ahora mismo'
    if (diffMinutes === 1) return 'Hace 1 minuto'
    if (diffMinutes < 60) return `Hace ${diffMinutes} minutos`

    const diffHours = Math.floor(diffMinutes / 60)
    if (diffHours === 1) return 'Hace 1 hora'
    if (diffHours < 24) return `Hace ${diffHours} horas`

    // Forzar zona horaria de Chile
    return date.toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Santiago'
    })
  } catch {
    return 'Fecha inválida'
  }
}

function formatHistoryDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    // Forzar zona horaria de Chile
    return date.toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Santiago'
    })
  } catch {
    return 'N/A'
  }
}

function getTypeLabel(type: string): string {
  const labels = {
    'ph_range': 'pH',
    'conductivity': 'Conductividad',
    'temperature': 'Temperatura',
    'sensor_disconnection': 'Conexión',
    'water_level': 'Nivel de Agua'
  }
  return labels[type as keyof typeof labels] || type
}

function getLevelLabel(level: string): string {
  const labels = {
    'critical': 'Crítica',
    'warning': 'Advertencia',
    'info': 'Información'
  }
  return labels[level as keyof typeof labels] || level
}

async function refreshAlerts(): Promise<void> {
  isLoading.value = true
  try {
    await alertStore.refresh()
  } finally {
    isLoading.value = false
  }
}

async function dismissAlert(alert: ActiveAlert): Promise<void> {
  dismissingAlerts.value.add(alert.id)

  try {
    await alertStore.dismissAlert(
      alert.id,
      `Cerrada desde gestión de alertas por ${authStore.user?.email}`
    )

    // Mostrar mensaje de éxito
    showSuccessMessage(`Alerta "${alert.title}" cerrada exitosamente`)

    // La alerta se removió automáticamente del store
    await refreshAlerts()

    // Actualizar el historial si es admin
    if (isAdmin.value) {
      await loadHistory()
    }
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Error desconocido al cerrar la alerta'
    showErrorMessage(`No se pudo cerrar la alerta: ${errorMsg}`)
  } finally {
    dismissingAlerts.value.delete(alert.id)
  }
}

function showSuccessMessage(message: string): void {
  // Por ahora usando alert, después se puede cambiar a toast
  alert(`✅ ${message}`)
}

function showErrorMessage(message: string): void {
  // Por ahora usando alert, después se puede cambiar a toast
  alert(`❌ ${message}`)
}

function applyFilters(): void {
  // Los filtros se aplican automáticamente via computed
}

async function loadHistory(): Promise<void> {
  if (!isAdmin.value) return

  loadingHistory.value = true
  try {
    const token = localStorage.getItem('userToken')
    if (!token) {
      console.error('No hay token de autenticación')
      throw new Error('No hay token de autenticación')
    }

    console.log('Cargando historial desde:', `${API_BASE_URL}/api/alerts/history?limit=50`)

    const response = await fetch(`${API_BASE_URL}/api/alerts/history?limit=50`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('Response status:', response.status)
    console.log('Response headers:', Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Error response:', errorText)
      throw new Error(`Error ${response.status}: ${response.statusText}`)
    }

    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      const responseText = await response.text()
      console.error('Respuesta no es JSON:', responseText.substring(0, 200))
      throw new Error('La respuesta del servidor no es JSON válido')
    }

    const data = await response.json()
    console.log('Data recibida:', data)

    // Mapear los datos del API al formato esperado por el componente
    alertHistory.value = data.history?.map((item: AlertHistoryApiItem) => ({
      id: item._id || item.alert_id,
      type: item.type,
      level: item.level,
      message: item.message,
      created_at: item.created_at,
      resolved_at: item.dismissed_at,
      duration_minutes: typeof item.duration_minutes === 'string' ? parseInt(item.duration_minutes) : item.duration_minutes,
      dismissed_by: item.dismissed_by
    })) || []

  } catch (error) {
    console.error('Error cargando historial:', error)
    alertHistory.value = []
  } finally {
    loadingHistory.value = false
  }
}

async function clearHistory(): Promise<void> {
  if (!isAdmin.value) return

  if (!confirm('¿Estás seguro de que quieres borrar TODO el historial de alertas? Esta acción no se puede deshacer.')) {
    return
  }

  clearingHistory.value = true
  try {
    const token = localStorage.getItem('userToken')
    if (!token) {
      throw new Error('No hay token de autenticación')
    }

    const response = await fetch(`${API_BASE_URL}/api/alerts/history/clear`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`)
    }

    // Limpiar el historial local
    alertHistory.value = []

  } catch (error) {
    console.error('Error borrando historial:', error)
    alert('Error al borrar el historial. Por favor, inténtalo de nuevo.')
  } finally {
    clearingHistory.value = false
  }
}

// Funciones de configuración de umbrales
async function loadThresholdConfig(): Promise<void> {
  if (!isAdmin.value) return

  loadingConfig.value = true
  configErrors.value = {}

  try {
    const token = localStorage.getItem('userToken')
    if (!token) {
      console.error('No hay token de autenticación')
      throw new Error('No hay token de autenticación')
    }

    console.log('Cargando configuración desde:', `${API_BASE_URL}/api/alerts/config`)

    const response = await fetch(`${API_BASE_URL}/api/alerts/config`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('Config response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Config error response:', errorText)
      throw new Error(`Error ${response.status}: ${response.statusText}`)
    }

    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      const responseText = await response.text()
      console.error('Config respuesta no es JSON:', responseText.substring(0, 200))
      throw new Error('La respuesta del servidor no es JSON válido')
    }

    const data = await response.json()
    console.log('Config data recibida:', data)

    // Convertir del formato del backend al formato del frontend
    const thresholds = data.thresholds

    thresholdConfig.value = {
      ph_min: thresholds?.ph?.warning_min || 4.5,
      ph_max: thresholds?.ph?.warning_max || 6.5,
      conductivity_max: thresholds?.conductivity?.warning_max || 1.5,
      water_level_min: thresholds?.water_level?.warning_min || 20,
      water_level_max: thresholds?.water_level?.warning_max || 85,
      temperature_min: thresholds?.temperature?.warning_min || 5,
      temperature_max: thresholds?.temperature?.warning_max || 35
    }

  } catch (error) {
    console.error('Error cargando configuración:', error)
    configMessage.value = 'Error al cargar la configuración'
  } finally {
    loadingConfig.value = false
  }
}

function validateConfig(): boolean {
  configErrors.value = {}
  let isValid = true

  // Validar pH
  if (thresholdConfig.value.ph_min < 0 || thresholdConfig.value.ph_min > 14) {
    configErrors.value.ph_min = 'El pH mínimo debe estar entre 0 y 14'
    isValid = false
  }
  if (thresholdConfig.value.ph_max < 0 || thresholdConfig.value.ph_max > 14) {
    configErrors.value.ph_max = 'El pH máximo debe estar entre 0 y 14'
    isValid = false
  }
  if (thresholdConfig.value.ph_min >= thresholdConfig.value.ph_max) {
    configErrors.value.ph_min = 'El pH mínimo debe ser menor que el máximo'
    isValid = false
  }

  // Validar conductividad
  if (thresholdConfig.value.conductivity_max <= 0) {
    configErrors.value.conductivity_max = 'La conductividad máxima debe ser mayor a 0'
    isValid = false
  }

  // Validar nivel de agua
  if (thresholdConfig.value.water_level_min < 0 || thresholdConfig.value.water_level_min > 100) {
    configErrors.value.water_level_min = 'El nivel mínimo debe estar entre 0% y 100%'
    isValid = false
  }
  if (thresholdConfig.value.water_level_max < 0 || thresholdConfig.value.water_level_max > 100) {
    configErrors.value.water_level_max = 'El nivel máximo debe estar entre 0% y 100%'
    isValid = false
  }
  if (thresholdConfig.value.water_level_min >= thresholdConfig.value.water_level_max) {
    configErrors.value.water_level_min = 'El nivel mínimo debe ser menor que el máximo'
    isValid = false
  }

  // Validar temperatura
  if (thresholdConfig.value.temperature_min >= thresholdConfig.value.temperature_max) {
    configErrors.value.temperature_min = 'La temperatura mínima debe ser menor que la máxima'
    isValid = false
  }

  return isValid
}

async function saveThresholdConfig(): Promise<void> {
  if (!isAdmin.value) return

  // Validar antes de guardar
  if (!validateConfig()) {
    configMessage.value = 'Por favor corrige los errores antes de guardar'
    return
  }

  savingConfig.value = true
  configMessage.value = ''

  try {
    const token = localStorage.getItem('userToken')
    if (!token) {
      throw new Error('No hay token de autenticación')
    }

    // Convertir el formato del frontend al formato que espera el backend
    const backendFormat = {
      thresholds: {
        ph: {
          warning_min: thresholdConfig.value.ph_min,
          warning_max: thresholdConfig.value.ph_max,
          critical_min: thresholdConfig.value.ph_min - 0.5,
          critical_max: thresholdConfig.value.ph_max + 0.5,
          optimal_min: thresholdConfig.value.ph_min + 0.5,
          optimal_max: thresholdConfig.value.ph_max - 0.5
        },
        conductivity: {
          warning_max: thresholdConfig.value.conductivity_max,
          critical_max: thresholdConfig.value.conductivity_max + 0.5,
          optimal_max: thresholdConfig.value.conductivity_max - 0.5,
          optimal_min: 0.0,
          warning_min: 0.0,
          critical_min: 0.0
        },
        water_level: {
          warning_min: thresholdConfig.value.water_level_min,
          warning_max: thresholdConfig.value.water_level_max,
          critical_min: thresholdConfig.value.water_level_min - 10,
          critical_max: thresholdConfig.value.water_level_max + 5,
          optimal_min: thresholdConfig.value.water_level_min + 10,
          optimal_max: thresholdConfig.value.water_level_max - 5
        },
        temperature: {
          warning_min: thresholdConfig.value.temperature_min,
          warning_max: thresholdConfig.value.temperature_max,
          critical_min: thresholdConfig.value.temperature_min - 5,
          critical_max: thresholdConfig.value.temperature_max + 5,
          optimal_min: thresholdConfig.value.temperature_min + 5,
          optimal_max: thresholdConfig.value.temperature_max - 5
        },
        sensor_timeout_warning: 6,
        sensor_timeout_critical: 15
      },
      updated_by: authStore.user?.email || 'admin',
      reason: 'Configuración actualizada desde la interfaz web'
    }

    const response = await fetch(`${API_BASE_URL}/api/alerts/config`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(backendFormat)
    })

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`)
    }

    configMessage.value = 'Configuración guardada exitosamente'

    // Cerrar modal después de un breve delay
    setTimeout(() => {
      showConfigModal.value = false
      configMessage.value = ''
    }, 1500)

  } catch (error) {
    console.error('Error guardando configuración:', error)
    configMessage.value = 'Error al guardar la configuración'
  } finally {
    savingConfig.value = false
  }
}

// Cargar configuración al abrir modal
function openConfigModal(): void {
  showConfigModal.value = true
  loadThresholdConfig()
}



// Watchers
watch(
  () => alertStore.activeAlerts.length,
  (newLength, oldLength) => {
    // Si se reduce el número de alertas (se cerró una) y somos admin, actualizar historial
    if (newLength < oldLength && isAdmin.value) {
      loadHistory()
    }
  }
)

// Lifecycle
onMounted(() => {
  refreshAlerts()

  // Usar nextTick para asegurar que el auth store esté inicializado
  nextTick(() => {
    if (isAdmin.value) {
      loadHistory()
    }
  })
})

// Watcher para cargar historial cuando el usuario se autentique como admin
watch(
  () => isAdmin.value,
  (isAdminNow) => {
    if (isAdminNow && alertHistory.value.length === 0) {
      loadHistory()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.alerts-management {
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* Header */
.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 0.5rem 0;
}

.page-title i {
  color: #e53e3e;
}

.page-description {
  color: #4a5568;
  font-size: 1rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

/* Botones de acción */
.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: 2px solid transparent;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.refresh-btn {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #2c5aa0;
}

.config-btn {
  background-color: #38a169;
  color: white;
}

.config-btn:hover:not(:disabled) {
  background-color: #2f855a;
}

.dismiss-btn {
  background: linear-gradient(135deg, #fc8181 0%, #e53e3e 100%);
  color: white;
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  box-shadow: 0 2px 8px rgba(229, 62, 62, 0.3);
}

.dismiss-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
  box-shadow: 0 4px 12px rgba(229, 62, 62, 0.4);
}

.danger-btn {
  background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
  color: white;
  border: 2px solid #c53030;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(197, 48, 48, 0.3);
}

.danger-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #c53030 0%, #9c2626 100%);
  border-color: #9c2626;
  box-shadow: 0 4px 12px rgba(197, 48, 48, 0.4);
}

.danger-btn:disabled {
  background: #a0aec0;
  border-color: #a0aec0;
  box-shadow: none;
}

.secondary-btn {
  background-color: #e2e8f0;
  color: #4a5568;
}

.secondary-btn:hover:not(:disabled) {
  background-color: #cbd5e0;
}

.primary-btn {
  background-color: #3182ce;
  color: white;
}

/* Resumen de alertas */
.alerts-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  gap: 1rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.summary-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.summary-card.critical {
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
  border-left: 4px solid #e53e3e;
}

.summary-card.warning {
  background: linear-gradient(135deg, #fffbeb 0%, #feebc8 100%);
  border-left: 4px solid #dd6b20;
}

.summary-card.info {
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
  border-left: 4px solid #3182ce;
}

.summary-card.success {
  background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
  border-left: 4px solid #38a169;
}

.card-icon i {
  font-size: 2rem;
}

.summary-card.critical .card-icon i { color: #e53e3e; }
.summary-card.warning .card-icon i { color: #dd6b20; }
.summary-card.info .card-icon i { color: #3182ce; }
.summary-card.success .card-icon i { color: #38a169; }

.card-content {
  flex: 1;
}

.card-number {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.card-label {
  font-size: 0.875rem;
  opacity: 0.8;
  margin-top: 0.25rem;
}

/* Filtros */
.filters-section {
  background-color: #f7fafc;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.filters-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 500;
  color: #4a5568;
  font-size: 0.875rem;
}

.filter-group select {
  padding: 0.5rem;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

/* Contenido de alertas */
.alerts-content {
  background: linear-gradient(145deg, #ffffff 0%, #fafafa 100%);
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  margin-bottom: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background-color: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-size: 1.25rem;
  color: #2d3748;
}

.last-update {
  font-size: 0.875rem;
  color: #718096;
}

/* Estados de carga y vacío */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.loading-state i {
  font-size: 2rem;
  color: #3182ce;
  margin-bottom: 1rem;
}

.empty-state i {
  font-size: 3rem;
  color: #38a169;
  margin-bottom: 1rem;
}

.empty-state h3 {
  color: #2d3748;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #718096;
  max-width: 400px;
}

/* Lista de alertas */
.alerts-list {
  max-height: 600px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  transition: all 0.3s ease;
  position: relative;
}

.alert-item:hover {
  background: linear-gradient(135deg, #f8faff 0%, #f1f5f9 100%);
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-main {
  display: flex;
  gap: 1rem;
  flex: 1;
  min-width: 0;
}

.alert-icon {
  flex-shrink: 0;
}

.alert-icon i {
  font-size: 1.5rem;
}

.alert-critical .alert-icon i { color: #e53e3e; }
.alert-warning .alert-icon i { color: #dd6b20; }
.alert-info .alert-icon i { color: #3182ce; }

.alert-info {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.alert-message {
  color: #4a5568;
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

.alert-details {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #718096;
}

.alert-threshold {
  font-size: 0.875rem;
  color: #4a5568;
  background-color: #f7fafc;
  padding: 0.5rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.alert-actions {
  flex-shrink: 0;
  margin-left: 1rem;
}

/* Historial */
.history-section {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.history-table {
  overflow-x: auto;
}

.history-table table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.history-table th {
  background-color: #f7fafc;
  font-weight: 600;
  color: #4a5568;
}

.level-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.level-critical { background-color: #fed7d7; color: #742a2a; }
.level-warning { background-color: #feebc8; color: #744210; }
.level-info { background-color: #bee3f8; color: #2a69ac; }

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  color: #2d3748;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #718096;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

/* Estilos del formulario de configuración */
.threshold-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  background-color: #f8fafc;
}

.form-section h4 {
  margin: 0 0 1rem 0;
  color: #2d3748;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-group label {
  font-weight: 600;
  color: #4a5568;
  font-size: 0.875rem;
}

.form-group input {
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.form-group input.error {
  border-color: #e53e3e;
  background-color: #fed7d7;
}

.error-text {
  color: #e53e3e;
  font-size: 0.75rem;
  font-weight: 500;
}

.config-message {
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
  text-align: center;
  margin-bottom: 1rem;
}

.config-message.success {
  background-color: #c6f6d5;
  color: #22543d;
  border: 1px solid #9ae6b4;
}

.config-message.error {
  background-color: #fed7d7;
  color: #742a2a;
  border: 1px solid #fc8181;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: #4a5568;
}

/* Responsive para formulario */
@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .alerts-header {
    flex-direction: column;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
    justify-content: stretch;
  }

  .action-btn {
    flex: 1;
  }

  .alert-item {
    flex-direction: column;
    gap: 1rem;
  }

  .alert-actions {
    width: 100%;
    margin-left: 0;
  }

  .alert-details {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
