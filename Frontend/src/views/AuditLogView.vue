<template>
  <div class="p-8">
    <!-- Header Card -->
    <div class="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 mb-6 shadow-lg">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
          <i class="pi pi-history text-2xl text-white"></i>
        </div>
        <div>
          <h1 class="text-2xl font-bold text-white m-0">Registro de Auditoría</h1>
          <p class="text-blue-100 text-sm mt-1">Historial de actividades del sistema</p>
        </div>
      </div>
    </div>

    <!-- Filters Card -->
    <div class="bg-white rounded-xl p-6 shadow-md mb-8 border border-gray-200">
      <div class="flex items-center gap-3 mb-6">
        <i class="pi pi-filter text-blue-600"></i>
        <h3 class="text-lg font-bold text-gray-800 m-0">Filtros</h3>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div>
          <label class="block mb-2 text-sm font-semibold text-gray-700">Usuario (Email)</label>
          <input
            v-model="filters.user_email"
            type="text"
            placeholder="Buscar por email..."
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
            @keyup.enter="applyFilters"
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-semibold text-gray-700">Tipo de Acción</label>
          <select
            v-model="filters.action"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm bg-white"
            @change="applyFilters"
          >
            <option value="">Todas las acciones</option>
            <option v-for="action in availableActions" :key="action.value" :value="action.value">
              {{ action.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="block mb-2 text-sm font-semibold text-gray-700">Estado</label>
          <select
            v-model="filters.success"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm bg-white"
            @change="applyFilters"
          >
            <option value="">Todos</option>
            <option value="true">Exitosas</option>
            <option value="false">Fallidas</option>
          </select>
        </div>

        <div>
          <label class="block mb-2 text-sm font-semibold text-gray-700">Desde</label>
          <input
            v-model="filters.start_date"
            type="datetime-local"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
            @change="applyFilters"
          />
        </div>

        <div>
          <label class="block mb-2 text-sm font-semibold text-gray-700">Hasta</label>
          <input
            v-model="filters.end_date"
            type="datetime-local"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm"
            @change="applyFilters"
          />
        </div>

        <div class="flex items-end">
          <button
            @click="clearFilters"
            class="w-full px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-all flex items-center justify-center gap-2 text-sm border border-gray-300"
          >
            <i class="pi pi-times text-sm"></i>
            Limpiar
          </button>
        </div>
      </div>
    </div>

    <!-- Audit Logs Table -->
    <div class="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
            <tr>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Fecha y Hora</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Usuario</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Acción</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Descripción</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Estado</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">IP</th>
              <th class="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Detalles</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-if="isLoading" class="hover:bg-gray-50 transition-colors">
              <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
                <div>Cargando registros...</div>
              </td>
            </tr>
            <tr v-else-if="auditLogs.length === 0" class="hover:bg-gray-50 transition-colors">
              <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                <i class="pi pi-info-circle text-2xl text-gray-400 mb-2"></i>
                <div>No se encontraron registros de auditoría</div>
              </td>
            </tr>
            <tr v-else v-for="log in auditLogs" :key="log.timestamp" class="hover:bg-blue-50 transition-colors">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {{ formatDate(log.timestamp) }}
              </td>
              <td class="px-6 py-4 text-sm text-gray-900">
                <div class="font-medium">{{ log.user_email || 'N/A' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getActionBadgeClass(log.action)" class="px-3 py-1 rounded-full text-xs font-semibold">
                  {{ formatActionLabel(log.action) }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-700">
                {{ log.description }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span v-if="log.success" class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit">
                  <i class="pi pi-check-circle"></i>
                  Exitoso
                </span>
                <span v-else class="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit">
                  <i class="pi pi-times-circle"></i>
                  Fallido
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                {{ log.ip_address || 'N/A' }}
              </td>
              <td class="px-6 py-4 text-center">
                <button
                  @click="openDetailsModal(log)"
                  class="text-blue-600 hover:text-blue-800 font-semibold text-sm hover:bg-blue-50 px-3 py-1 rounded transition-all"
                  title="Ver detalles"
                >
                  <i class="pi pi-eye"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="!isLoading && auditLogs.length > 0" class="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="text-sm text-gray-700">
            Página <span class="font-semibold">{{ pagination.page }}</span> de <span class="font-semibold">{{ Math.ceil(pagination.total / pagination.page_size) }}</span>
            ({{ pagination.total }} registros)
          </div>
          <div class="flex items-center gap-2">
            <label for="pageSize" class="text-sm text-gray-700">Items por página:</label>
            <select
              id="pageSize"
              v-model.number="pagination.page_size"
              @change="changePageSize"
              class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            >
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
          </div>
        </div>
        <div class="flex gap-2">
          <button
            @click="previousPage"
            :disabled="pagination.page === 1"
            class="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
          >
            <i class="pi pi-chevron-left"></i>
            Anterior
          </button>
          <button
            @click="nextPage"
            :disabled="pagination.page >= Math.ceil(pagination.total / pagination.page_size)"
            class="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
          >
            Siguiente
            <i class="pi pi-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="showDetailsModal" class="fixed top-0 left-0 w-full h-full bg-black/60 backdrop-blur-sm flex justify-center items-center z-[1000]" @click.self="showDetailsModal = false">
      <div class="bg-white rounded-xl w-[90%] max-w-[700px] max-h-[90vh] overflow-y-auto shadow-2xl border border-gray-200">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-gradient-to-r from-blue-500 to-blue-600 p-6 border-b border-blue-700">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <i class="pi pi-info-circle text-white text-lg"></i>
              </div>
              <h2 class="text-xl font-bold text-white m-0">Detalles del Registro</h2>
            </div>
            <button
              @click="showDetailsModal = false"
              class="text-white hover:bg-white/20 rounded-lg p-2 transition-all"
              title="Cerrar"
            >
              <i class="pi pi-times text-xl"></i>
            </button>
          </div>
        </div>

        <!-- Modal Body -->
        <div v-if="selectedLog" class="p-6 space-y-6">
          <!-- User Info -->
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <i class="pi pi-user text-blue-600"></i>
              Información del Usuario
            </h3>
            <div class="space-y-2">
              <div class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">Email:</span>
                <span class="text-sm text-gray-900 font-medium">{{ selectedLog.user_email || 'N/A' }}</span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">ID:</span>
                <span class="text-sm text-gray-900 font-mono">{{ selectedLog.user_id || 'N/A' }}</span>
              </div>
            </div>
          </div>

          <!-- Action Info -->
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <i class="pi pi-bolt text-blue-600"></i>
              Información de la Acción
            </h3>
            <div class="space-y-2">
              <div class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">Acción:</span>
                <span :class="getActionBadgeClass(selectedLog.action)" class="px-3 py-1 rounded-full text-xs font-semibold">
                  {{ formatActionLabel(selectedLog.action) }}
                </span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">Fecha:</span>
                <span class="text-sm text-gray-900">{{ formatDate(selectedLog.timestamp) }}</span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">Estado:</span>
                <span v-if="selectedLog.success" class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit">
                  <i class="pi pi-check-circle"></i>
                  Exitoso
                </span>
                <span v-else class="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit">
                  <i class="pi pi-times-circle"></i>
                  Fallido
                </span>
              </div>
              <div class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">Descripción:</span>
                <span class="text-sm text-gray-900 text-right max-w-md">{{ selectedLog.description }}</span>
              </div>
            </div>
          </div>

          <!-- Network Info -->
          <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <i class="pi pi-globe text-blue-600"></i>
              Información de Red
            </h3>
            <div class="space-y-2">
              <div class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">Dirección IP:</span>
                <span class="text-sm text-gray-900 font-mono">{{ selectedLog.ip_address || 'N/A' }}</span>
              </div>
              <div class="flex flex-col gap-1">
                <span class="text-sm font-semibold text-gray-600">User Agent:</span>
                <span class="text-xs text-gray-700 bg-white p-2 rounded border border-gray-200 break-all font-mono">
                  {{ selectedLog.user_agent || 'N/A' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Resource Info (if available) -->
          <div v-if="selectedLog.resource_type || selectedLog.resource_id" class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <i class="pi pi-file text-blue-600"></i>
              Recurso Afectado
            </h3>
            <div class="space-y-2">
              <div v-if="selectedLog.resource_type" class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">Tipo:</span>
                <span class="text-sm text-gray-900">{{ selectedLog.resource_type }}</span>
              </div>
              <div v-if="selectedLog.resource_id" class="flex justify-between items-start">
                <span class="text-sm font-semibold text-gray-600">ID:</span>
                <span class="text-sm text-gray-900 font-mono">{{ selectedLog.resource_id }}</span>
              </div>
            </div>
          </div>

          <!-- Additional Details (if available) -->
          <div v-if="selectedLog.details && Object.keys(selectedLog.details).length > 0" class="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 class="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 flex items-center gap-2">
              <i class="pi pi-list text-blue-600"></i>
              Detalles Adicionales
            </h3>
            <pre class="text-xs text-gray-800 bg-white p-4 rounded border border-gray-200 overflow-x-auto font-mono">{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '@/config/api';

interface AuditLog {
  user_id?: string;
  user_email?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  description: string;
  ip_address?: string;
  user_agent?: string;
  details?: Record<string, any>;
  timestamp: string;
  success: boolean;
}

interface Statistics {
  total_logs: number;
  failed_actions: number;
  success_rate: number;
  action_counts: Record<string, number>;
  top_users: Array<{ user_email: string; count: number }>;
}

interface Pagination {
  page: number;
  page_size: number;
  total: number;
}

const auditLogs = ref<AuditLog[]>([]);
const statistics = ref<Statistics>({
  total_logs: 0,
  failed_actions: 0,
  success_rate: 0,
  action_counts: {},
  top_users: []
});
const pagination = ref<Pagination>({
  page: 1,
  page_size: 10,
  total: 0
});
const isLoading = ref(false);
const showDetailsModal = ref(false);
const selectedLog = ref<AuditLog | null>(null);

const filters = ref({
  user_email: '',
  action: '',
  start_date: '',
  end_date: '',
  success: ''
});

const availableActions = ref<Array<{ label: string; value: string }>>([]);

onMounted(() => {
  loadAuditLogs();
  loadStatistics();
  loadAvailableActions();
});

async function loadAuditLogs() {
  isLoading.value = true;
  const token = localStorage.getItem('userToken');

  try {
    const params = new URLSearchParams({
      page: pagination.value.page.toString(),
      page_size: pagination.value.page_size.toString()
    });

    if (filters.value.user_email) params.append('user_email', filters.value.user_email);
    if (filters.value.action) params.append('action', filters.value.action);
    if (filters.value.start_date) params.append('start_date', new Date(filters.value.start_date).toISOString());
    if (filters.value.end_date) params.append('end_date', new Date(filters.value.end_date).toISOString());
    if (filters.value.success) params.append('success', filters.value.success);

    const response = await fetch(`${API_BASE_URL}/api/audit/logs?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error('Error al cargar los logs de auditoría');

    const data = await response.json();
    auditLogs.value = data.logs;
    pagination.value.total = data.total;
  } catch (error) {
    console.error('Error loading audit logs:', error);
  } finally {
    isLoading.value = false;
  }
}

async function loadStatistics() {
  const token = localStorage.getItem('userToken');

  try {
    const response = await fetch(`${API_BASE_URL}/api/audit/statistics`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error('Error al cargar estadísticas');

    statistics.value = await response.json();
  } catch (error) {
    console.error('Error loading statistics:', error);
  }
}

async function loadAvailableActions() {
  const token = localStorage.getItem('userToken');

  try {
    const response = await fetch(`${API_BASE_URL}/api/audit/actions`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error('Error al cargar acciones');

    const data = await response.json();
    availableActions.value = data.actions || [];
  } catch (error) {
    console.error('Error loading actions:', error);
  }
}

function applyFilters() {
  pagination.value.page = 1;
  loadAuditLogs();
}

function clearFilters() {
  filters.value = {
    user_email: '',
    action: '',
    start_date: '',
    end_date: '',
    success: ''
  };
  applyFilters();
}

function nextPage() {
  if (pagination.value.page < Math.ceil(pagination.value.total / pagination.value.page_size)) {
    pagination.value.page++;
    loadAuditLogs();
  }
}

function previousPage() {
  if (pagination.value.page > 1) {
    pagination.value.page--;
    loadAuditLogs();
  }
}

function changePageSize() {
  // Reset a la primera página cuando se cambia el tamaño de página
  pagination.value.page = 1;
  loadAuditLogs();
}

function openDetailsModal(log: AuditLog) {
  selectedLog.value = log;
  showDetailsModal.value = true;
}

function formatDate(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('es-CL', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
}

function formatActionLabel(action: string): string {
  const labels: Record<string, string> = {
    'login': 'Login',
    'login_failed': 'Login Fallido',
    'logout': 'Logout',
    'user_created': 'Usuario Creado',
    'user_updated': 'Usuario Actualizado',
    'user_deleted': 'Usuario Eliminado',
    'password_changed': 'Contraseña Cambiada',
    'password_reset_requested': 'Reset Contraseña Solicitado',
    'password_reset_completed': 'Reset Contraseña Completado',
    'alert_threshold_updated': 'Umbral Alerta Actualizado',
    'alert_dismissed': 'Alerta Descartada',
    'notification_sent': 'Notificación Enviada',
    'sensor_data_received': 'Datos Sensor Recibidos',
    'system_config_updated': 'Config. Sistema Actualizada'
  };
  return labels[action] || action;
}

function getActionBadgeClass(action: string): string {
  const classes: Record<string, string> = {
    'login': 'bg-green-100 text-green-800',
    'login_failed': 'bg-red-100 text-red-800',
    'logout': 'bg-gray-100 text-gray-800',
    'user_created': 'bg-blue-100 text-blue-800',
    'user_updated': 'bg-yellow-100 text-yellow-800',
    'user_deleted': 'bg-red-100 text-red-800',
    'password_changed': 'bg-purple-100 text-purple-800',
    'password_reset_requested': 'bg-orange-100 text-orange-800',
    'password_reset_completed': 'bg-green-100 text-green-800',
    'alert_threshold_updated': 'bg-indigo-100 text-indigo-800',
    'alert_dismissed': 'bg-gray-100 text-gray-800',
    'notification_sent': 'bg-cyan-100 text-cyan-800',
    'sensor_data_received': 'bg-teal-100 text-teal-800',
    'system_config_updated': 'bg-pink-100 text-pink-800'
  };
  return classes[action] || 'bg-gray-100 text-gray-800';
}
</script>
