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
          @click="showConfigModal = true"
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
          <!-- Aquí iría el formulario de configuración de umbrales -->
          <p>Formulario de configuración de umbrales (pendiente implementar)</p>
        </div>

        <div class="modal-footer">
          <button @click="showConfigModal = false" class="action-btn secondary-btn">
            Cancelar
          </button>
          <button @click="saveThresholdConfig" class="action-btn primary-btn">
            Guardar Cambios
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
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
const dismissingAlerts = ref(new Set<string>())
const alertHistory = ref<AlertHistoryItem[]>([])

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
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diffMs / 60000)

    if (diffMinutes === 0) return 'Ahora mismo'
    if (diffMinutes === 1) return 'Hace 1 minuto'
    if (diffMinutes < 60) return `Hace ${diffMinutes} minutos`

    const diffHours = Math.floor(diffMinutes / 60)
    if (diffHours === 1) return 'Hace 1 hora'
    if (diffHours < 24) return `Hace ${diffHours} horas`

    return date.toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return 'Fecha inválida'
  }
}

function formatHistoryDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
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
      throw new Error('No hay token de autenticación')
    }

    const response = await fetch(`${API_BASE_URL}/api/alerts/history?limit=50`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()

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

function saveThresholdConfig(): void {
  // Implementar guardado de configuración
  showConfigModal.value = false
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
  // Cargar historial automáticamente si es admin
  if (isAdmin.value) {
    loadHistory()
  }
})
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
