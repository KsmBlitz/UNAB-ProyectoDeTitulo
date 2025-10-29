<template>
  <div class="p-8">
    <!-- Header de la vista -->
    <div class="bg-white rounded-2xl p-6 shadow-lg border border-gray-200 mb-8">
      <div class="flex justify-between items-start flex-wrap gap-4">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center shadow-md">
            <i class="pi pi-bell text-xl text-white"></i>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-800 m-0 mb-1">
              Gestión de Alertas del Sistema
            </h1>
            <p class="text-gray-600 m-0 text-sm">
              Monitoreo en tiempo real de condiciones críticas para el cultivo de arándanos
            </p>
          </div>
        </div>

        <div class="flex gap-3 flex-wrap">
          <button
            @click="refreshAlerts"
            class="px-4 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold cursor-pointer transition-all hover:from-blue-600 hover:to-blue-700 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2 shadow-md hover:shadow-lg text-sm"
            :disabled="isLoading"
            title="Actualizar alertas"
          >
            <i class="pi pi-refresh text-sm" :class="{ 'pi-spin': isLoading }"></i>
            Actualizar
          </button>

          <button
            v-if="isAdmin"
            @click="openConfigModal"
            class="px-4 py-2.5 bg-slate-600 text-white rounded-lg font-semibold cursor-pointer transition-all hover:bg-slate-700 flex items-center gap-2 shadow-md hover:shadow-lg text-sm"
            title="Configurar umbrales de alertas"
          >
            <i class="pi pi-cog text-sm"></i>
            Configurar Umbrales
          </button>
        </div>
      </div>
    </div>

    <!-- Resumen de alertas -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div v-if="alertStore.summary.critical > 0" class="bg-white border-l-4 border-red-500 rounded-xl p-6 shadow-lg">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-lg flex items-center justify-center shadow-md">
            <i class="pi pi-exclamation-triangle text-xl text-white"></i>
          </div>
          <div>
            <div class="text-3xl font-bold text-gray-800 mb-1">{{ alertStore.summary.critical }}</div>
            <div class="text-sm text-gray-600 font-medium">Alertas Críticas</div>
          </div>
        </div>
      </div>

      <div v-if="alertStore.summary.warning > 0" class="bg-white border-l-4 border-orange-500 rounded-xl p-6 shadow-lg">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center shadow-md">
            <i class="pi pi-exclamation-circle text-xl text-white"></i>
          </div>
          <div>
            <div class="text-3xl font-bold text-gray-800 mb-1">{{ alertStore.summary.warning }}</div>
            <div class="text-sm text-gray-600 font-medium">Advertencias</div>
          </div>
        </div>
      </div>

      <div v-if="alertStore.summary.info > 0" class="bg-white border-l-4 border-blue-500 rounded-xl p-6 shadow-lg">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-md">
            <i class="pi pi-info-circle text-xl text-white"></i>
          </div>
          <div>
            <div class="text-3xl font-bold text-gray-800 mb-1">{{ alertStore.summary.info }}</div>
            <div class="text-sm text-gray-600 font-medium">Informativas</div>
          </div>
        </div>
      </div>

      <div v-if="!alertStore.hasAnyAlerts" class="bg-white border-l-4 border-green-500 rounded-xl p-6 shadow-lg">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center shadow-md">
            <i class="pi pi-check-circle text-xl text-white"></i>
          </div>
          <div>
            <div class="text-3xl font-bold text-gray-800 mb-1">0</div>
            <div class="text-sm text-gray-600 font-medium">Todo Normal</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-xl p-6 shadow-md mb-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label class="block mb-2 font-semibold text-gray-700">Nivel de Alerta:</label>
          <select
            v-model="filters.level"
            @change="applyFilters"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Todos los niveles</option>
            <option value="critical">Críticas</option>
            <option value="warning">Advertencias</option>
            <option value="info">Informativas</option>
          </select>
        </div>

        <div>
          <label class="block mb-2 font-semibold text-gray-700">Tipo de Alerta:</label>
          <select
            v-model="filters.type"
            @change="applyFilters"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Todos los tipos</option>
            <option value="ph_range">pH fuera de rango</option>
            <option value="conductivity">Conductividad elevada</option>
            <option value="temperature">Temperatura anormal</option>
            <option value="sensor_disconnection">Sensor desconectado</option>
          </select>
        </div>

        <div>
          <label class="block mb-2 font-semibold text-gray-700">Período:</label>
          <select
            v-model="filters.period"
            @change="applyFilters"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="today">Hoy</option>
            <option value="week">Esta semana</option>
            <option value="month">Este mes</option>
            <option value="all">Todo el historial</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Lista de alertas activas -->
    <div class="bg-white rounded-xl p-6 shadow-md mb-8">
      <div class="flex justify-between items-center mb-6 pb-4 border-b-2 border-gray-100">
        <h2 class="text-2xl font-bold text-gray-800 flex items-center gap-2 m-0">
          <i class="pi pi-bell"></i>
          Alertas Activas ({{ filteredActiveAlerts.length }})
        </h2>
        <div class="text-sm text-gray-500">
          Última actualización: {{ alertStore.lastUpdateFormatted }}
        </div>
      </div>

      <!-- Estado de carga o vacío -->
      <div v-if="isLoading" class="flex items-center justify-center gap-3 py-12 text-gray-500">
        <i class="pi pi-spin pi-spinner text-2xl"></i>
        <span>Cargando alertas...</span>
      </div>

      <div v-else-if="filteredActiveAlerts.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
        <i class="pi pi-check-circle text-6xl text-success-500 mb-4"></i>
        <h3 class="text-xl font-bold text-gray-800 mb-2">No hay alertas activas</h3>
        <p class="text-gray-600 max-w-md">Todas las condiciones están dentro de los rangos normales para el cultivo de arándanos.</p>
      </div>

      <!-- Lista de alertas -->
      <div v-else class="space-y-4">
        <div
          v-for="alert in filteredActiveAlerts"
          :key="alert.id"
          class="border-l-8 rounded-xl p-7 transition-all hover:shadow-xl bg-white"
          :class="{
            'border-red-500 bg-red-50/40': alert.level === 'critical',
            'border-orange-400 bg-orange-50/40': alert.level === 'warning',
            'border-blue-500 bg-blue-50/40': alert.level === 'info'
          }"
        >
          <div class="flex gap-6 items-start">
            <div class="text-4xl flex-shrink-0 mt-1" :class="{
              'text-red-500': alert.level === 'critical',
              'text-orange-400': alert.level === 'warning',
              'text-blue-500': alert.level === 'info'
            }">
              <i :class="getAlertIcon(alert.level)"></i>
            </div>

            <div class="flex-grow">
              <div class="text-xl font-semibold mb-2" :class="{
                'text-red-700': alert.level === 'critical',
                'text-orange-700': alert.level === 'warning',
                'text-blue-700': alert.level === 'info'
              }">{{ alert.title }}</div>
              <div class="text-gray-700 mb-4">{{ alert.message }}</div>
              <div class="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                <span class="flex items-center gap-2">
                  <i class="pi pi-map-marker"></i>
                  {{ alert.location }}
                </span>
                <span v-if="alert.sensor_id" class="flex items-center gap-2">
                  <i class="pi pi-microchip"></i>
                  Sensor: {{ alert.sensor_id }}
                </span>
                <span class="flex items-center gap-2">
                  <i class="pi pi-clock"></i>
                  {{ formatAlertTime(alert.created_at) }}
                </span>
              </div>
              <div class="flex items-center gap-2 text-sm bg-white/50 rounded px-3 py-2 inline-flex">
                <i class="pi pi-info-circle"></i>
                {{ alert.threshold_info }}
              </div>
            </div>

            <div class="flex-shrink-0">
              <button
                @click="dismissAlert(alert)"
                class="px-4 py-2 bg-gray-600 text-white border-none rounded-md font-medium cursor-pointer transition-all hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
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
    </div>

    <!-- Historial de alertas (solo para admin) -->
    <div v-if="isAdmin" class="bg-white rounded-xl p-6 shadow-md mb-8">
      <div class="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
        <h2 class="text-2xl font-bold text-gray-800 flex items-center gap-3">
          <i class="pi pi-history text-primary-500"></i>
          Historial de Alertas
        </h2>
        <div class="flex gap-3">
          <button
            @click="loadHistory"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="loadingHistory"
          >
            <i class="pi pi-refresh" :class="{ 'pi-spin': loadingHistory }"></i>
            Refrescar Historial
          </button>

          <button
            @click="clearHistory"
            class="px-4 py-2 bg-danger-500 text-white rounded-lg hover:bg-danger-600 transition-colors duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="clearingHistory || alertHistory.length === 0"
            title="Borrar todo el historial (solo admin)"
          >
            <i class="pi pi-trash" :class="{ 'pi-spin': clearingHistory }"></i>
            {{ clearingHistory ? 'Borrando...' : 'Borrar Historial' }}
          </button>
        </div>
      </div>

      <div v-if="alertHistory.length > 0" class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Fecha/Hora</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Tipo</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Nivel</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Mensaje</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Duración</th>
              <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Cerrada por</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="historyItem in alertHistory" :key="historyItem.id" class="hover:bg-gray-50 transition-colors duration-150">
              <td class="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">{{ formatHistoryDate(historyItem.created_at) }}</td>
              <td class="px-6 py-4 text-sm text-gray-700">{{ getTypeLabel(historyItem.type) }}</td>
              <td class="px-6 py-4 text-sm">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border"
                      :class="{
                        'bg-red-50 border-red-400 text-red-700': historyItem.level === 'critical',
                        'bg-orange-50 border-orange-400 text-orange-700': historyItem.level === 'warning',
                        'bg-blue-50 border-blue-400 text-blue-700': historyItem.level === 'info'
                      }">
                  {{ getLevelLabel(historyItem.level) }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-700">{{ historyItem.message }}</td>
              <td class="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">{{ historyItem.duration_minutes || 0 }} min</td>
              <td class="px-6 py-4 text-sm text-gray-600">{{ historyItem.dismissed_by || 'Auto-resuelta' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal de configuración de umbrales (solo admin) -->
    <div v-if="showConfigModal && isAdmin" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click="showConfigModal = false">
      <div class="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden" @click.stop>
        <div class="flex justify-between items-center p-6 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-primary-100">
          <h3 class="text-2xl font-bold text-gray-800">Configuración de Umbrales para Arándanos</h3>
          <button @click="showConfigModal = false" class="text-gray-500 hover:text-gray-700 transition-colors p-2 hover:bg-white rounded-lg">
            <i class="pi pi-times text-xl"></i>
          </button>
        </div>

        <div class="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          <div v-if="loadingConfig" class="flex items-center justify-center gap-3 py-12">
            <i class="pi pi-spin pi-spinner text-3xl text-primary-500"></i>
            <span class="text-gray-600 text-lg">Cargando configuración...</span>
          </div>

          <form v-else @submit.prevent="saveThresholdConfig" class="space-y-6">
            <!-- Mensaje de estado -->
            <div v-if="configMessage" class="mb-6 p-4 rounded-lg"
                 :class="{
                   'bg-success-50 text-success-800 border border-success-200': configMessage.includes('exitosamente'),
                   'bg-danger-50 text-danger-800 border border-danger-200': !configMessage.includes('exitosamente')
                 }">
              {{ configMessage }}
            </div>

            <!-- Configuración de pH -->
            <div class="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <i class="pi pi-chart-bar text-primary-500"></i>
                Niveles de pH
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label for="ph_min" class="block text-sm font-semibold text-gray-700 mb-2">pH Mínimo:</label>
                  <input
                    id="ph_min"
                    v-model.number="thresholdConfig.ph_min"
                    type="number"
                    step="0.1"
                    min="0"
                    max="14"
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    :class="configErrors.ph_min ? 'border-danger-500' : 'border-gray-300'"
                  >
                  <span v-if="configErrors.ph_min" class="text-sm text-danger-600 mt-1 block">{{ configErrors.ph_min }}</span>
                </div>
                <div>
                  <label for="ph_max" class="block text-sm font-semibold text-gray-700 mb-2">pH Máximo:</label>
                  <input
                    id="ph_max"
                    v-model.number="thresholdConfig.ph_max"
                    type="number"
                    step="0.1"
                    min="0"
                    max="14"
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    :class="configErrors.ph_max ? 'border-danger-500' : 'border-gray-300'"
                  >
                  <span v-if="configErrors.ph_max" class="text-sm text-danger-600 mt-1 block">{{ configErrors.ph_max }}</span>
                </div>
              </div>
            </div>

            <!-- Configuración de Conductividad -->
            <div class="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <i class="pi pi-bolt text-warning-500"></i>
                Conductividad Eléctrica
              </h4>
              <div>
                <label for="conductivity_max" class="block text-sm font-semibold text-gray-700 mb-2">Conductividad Máxima (dS/m):</label>
                <input
                  id="conductivity_max"
                  v-model.number="thresholdConfig.conductivity_max"
                  type="number"
                  step="0.1"
                  min="0"
                  class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                  :class="configErrors.conductivity_max ? 'border-danger-500' : 'border-gray-300'"
                >
                <span v-if="configErrors.conductivity_max" class="text-sm text-danger-600 mt-1 block">{{ configErrors.conductivity_max }}</span>
              </div>
            </div>

            <!-- Configuración de Nivel de Agua -->
            <div class="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <i class="pi pi-tint text-blue-500"></i>
                Nivel de Agua
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label for="water_level_min" class="block text-sm font-semibold text-gray-700 mb-2">Nivel Mínimo (%):</label>
                  <input
                    id="water_level_min"
                    v-model.number="thresholdConfig.water_level_min"
                    type="number"
                    min="0"
                    max="100"
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    :class="configErrors.water_level_min ? 'border-danger-500' : 'border-gray-300'"
                  >
                  <span v-if="configErrors.water_level_min" class="text-sm text-danger-600 mt-1 block">{{ configErrors.water_level_min }}</span>
                </div>
                <div>
                  <label for="water_level_max" class="block text-sm font-semibold text-gray-700 mb-2">Nivel Máximo (%):</label>
                  <input
                    id="water_level_max"
                    v-model.number="thresholdConfig.water_level_max"
                    type="number"
                    min="0"
                    max="100"
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    :class="configErrors.water_level_max ? 'border-danger-500' : 'border-gray-300'"
                  >
                  <span v-if="configErrors.water_level_max" class="text-sm text-danger-600 mt-1 block">{{ configErrors.water_level_max }}</span>
                </div>
              </div>
            </div>

            <!-- Configuración de Temperatura -->
            <div class="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h4 class="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <i class="pi pi-sun text-warning-500"></i>
                Temperatura
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label for="temperature_min" class="block text-sm font-semibold text-gray-700 mb-2">Temperatura Mínima (°C):</label>
                  <input
                    id="temperature_min"
                    v-model.number="thresholdConfig.temperature_min"
                    type="number"
                    step="0.1"
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    :class="configErrors.temperature_min ? 'border-danger-500' : 'border-gray-300'"
                  >
                  <span v-if="configErrors.temperature_min" class="text-sm text-danger-600 mt-1 block">{{ configErrors.temperature_min }}</span>
                </div>
                <div>
                  <label for="temperature_max" class="block text-sm font-semibold text-gray-700 mb-2">Temperatura Máxima (°C):</label>
                  <input
                    id="temperature_max"
                    v-model.number="thresholdConfig.temperature_max"
                    type="number"
                    step="0.1"
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                    :class="configErrors.temperature_max ? 'border-danger-500' : 'border-gray-300'"
                  >
                  <span v-if="configErrors.temperature_max" class="text-sm text-danger-600 mt-1 block">{{ configErrors.temperature_max }}</span>
                </div>
              </div>
            </div>
          </form>
        </div>

        <div class="flex justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button @click="showConfigModal = false" class="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed" :disabled="savingConfig">
            Cancelar
          </button>
          <button @click="saveThresholdConfig" class="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed" :disabled="loadingConfig || savingConfig">
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
