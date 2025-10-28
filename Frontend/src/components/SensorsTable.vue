<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

defineOptions({
  name: 'SensorsTable'
});

interface SensorReading {
  uid: string;
  last_value: {
    value: number;
    unit: string;
    type: string;
  };
  status: 'online' | 'offline' | 'warning';
  location: string;
  last_reading: string;
  minutes_since_reading: number;
}

const sensors = ref<SensorReading[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const fetchSensorsStatus = async () => {
  isLoading.value = true;
  error.value = null;

  const token = localStorage.getItem('userToken');

  if (!token) {
    error.value = 'No hay token de autenticación';
    isLoading.value = false;
    return;
  }

  try {
    // ✅ CAMBIAR URL
    const response = await fetch(`${API_BASE_URL}/api/sensors/individual`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expirado o inválido
        localStorage.removeItem('userToken');
        window.location.href = '/login';
        return;
      }
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    const sensorsData = await response.json();

    // Mapear datos del backend
    sensors.value = sensorsData.map((sensor: any) => ({
      uid: sensor.uid,
      last_value: sensor.last_value,
      status: sensor.status,
      location: sensor.location,
      last_reading: sensor.last_reading,
      minutes_since_reading: sensor.minutes_since_reading
    }));

  } catch (err) {
    console.error('Error al cargar sensores:', err);

    if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
      error.value = 'No se puede conectar al servidor. Verifica que el backend esté ejecutándose.';
    } else {
      error.value = err instanceof Error ? err.message : 'Error desconocido al cargar sensores.';
    }
  } finally {
    isLoading.value = false;
  }
};

const formatLastReading = (isoString: string) => {
  const date = new Date(isoString);
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'online': return 'Conectado';
    case 'warning': return 'Advertencia';
    case 'offline': return 'Desconectado';
    default: return 'Desconocido';
  }
};

onMounted(fetchSensorsStatus);

// Auto-refresh cada 30 segundos
setInterval(fetchSensorsStatus, 30000);

// Exponer la función al componente padre
defineExpose({
  fetchSensorsStatus
});
</script>

<template>
  <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
    <!-- Header con botón actualizar -->
    <div class="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
      <div class="flex gap-6">
        <div class="flex flex-col items-center gap-1">
          <span class="text-2xl font-bold text-green-600">{{ sensors.filter(s => s.status === 'online').length }}</span>
          <span class="text-xs text-gray-600 uppercase tracking-wider font-medium">Conectados</span>
        </div>
        <div class="flex flex-col items-center gap-1">
          <span class="text-2xl font-bold text-orange-500">{{ sensors.filter(s => s.status === 'warning').length }}</span>
          <span class="text-xs text-gray-600 uppercase tracking-wider font-medium">Advertencia</span>
        </div>
        <div class="flex flex-col items-center gap-1">
          <span class="text-2xl font-bold text-red-600">{{ sensors.filter(s => s.status === 'offline').length }}</span>
          <span class="text-xs text-gray-600 uppercase tracking-wider font-medium">Desconectados</span>
        </div>
      </div>
      <button
        @click="fetchSensorsStatus"
        class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all shadow-md hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
        :disabled="isLoading"
      >
        <i class="pi text-sm" :class="isLoading ? 'pi-spin pi-spinner' : 'pi-refresh'"></i>
        <span class="text-sm font-medium">Actualizar</span>
      </button>
    </div>

    <div v-if="error" class="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 mb-4">
      <i class="pi pi-info-circle text-lg"></i>
      <p class="text-sm">{{ error }}</p>
    </div>

    <div v-if="isLoading" class="flex items-center justify-center gap-2 py-12 text-gray-500">
      <i class="pi pi-spin pi-spinner text-lg"></i>
      <span class="text-sm">Cargando estado de sensores...</span>
    </div>

    <!-- Vista de tabla para desktop -->
    <div v-else class="hidden lg:block overflow-hidden rounded-lg border border-gray-200">
      <table class="w-full border-collapse">
        <thead>
          <tr class="bg-gradient-to-r from-slate-50 to-gray-100">
            <th class="text-left p-4 font-semibold text-gray-700 text-xs uppercase tracking-wider border-b border-gray-300">UID Sensor (MAC)</th>
            <th class="text-left p-4 font-semibold text-gray-700 text-xs uppercase tracking-wider border-b border-gray-300">Últimos Valores</th>
            <th class="text-left p-4 font-semibold text-gray-700 text-xs uppercase tracking-wider border-b border-gray-300">Estado</th>
            <th class="text-left p-4 font-semibold text-gray-700 text-xs uppercase tracking-wider border-b border-gray-300">Ubicación</th>
            <th class="text-left p-4 font-semibold text-gray-700 text-xs uppercase tracking-wider border-b border-gray-300">Última Lectura</th>
          </tr>
        </thead>
        <tbody class="bg-white">
          <tr v-for="sensor in sensors" :key="sensor.uid" class="hover:bg-blue-50/50 transition-colors">
            <!-- UID/MAC -->
            <td class="p-4 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
                  <i class="pi pi-microchip text-sm text-white"></i>
                </div>
                <code class="bg-gray-100 px-2.5 py-1 rounded-md text-xs font-semibold font-mono text-gray-700">{{ sensor.uid }}</code>
              </div>
            </td>

            <!-- Últimos valores -->
            <td class="p-4 border-b border-gray-100 text-center">
              <div>
                <span class="text-xl font-bold text-gray-900">{{ sensor.last_value.value }}</span>
                <span class="text-sm text-gray-600 ml-1">{{ sensor.last_value.unit }}</span>
                <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">{{ sensor.last_value.type }}</div>
              </div>
            </td>

            <!-- Estado -->
            <td class="p-4 border-b border-gray-100">
              <div
                class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold"
                :class="{
                  'bg-green-50 text-green-700 border border-green-200': sensor.status === 'online',
                  'bg-orange-50 text-orange-700 border border-orange-200': sensor.status === 'warning',
                  'bg-red-50 text-red-700 border border-red-200': sensor.status === 'offline',
                  'bg-gray-50 text-gray-700 border border-gray-200': sensor.status !== 'online' && sensor.status !== 'warning' && sensor.status !== 'offline'
                }"
              >
                <i class="pi pi-circle-fill text-[6px]"></i>
                <span>{{ getStatusText(sensor.status) }}</span>
              </div>
              <div v-if="sensor.minutes_since_reading > 0" class="text-xs text-gray-500 mt-1">
                {{ sensor.minutes_since_reading }} min sin datos
              </div>
            </td>

            <!-- Ubicación -->
            <td class="p-4 border-b border-gray-100">
              <div class="flex items-center gap-2 text-gray-700">
                <i class="pi pi-map-marker text-sm text-red-500"></i>
                <span class="text-sm">{{ sensor.location }}</span>
              </div>
            </td>

            <!-- Última lectura -->
            <td class="p-4 border-b border-gray-100 text-gray-600 text-xs">
              <div class="flex items-center gap-2">
                <i class="pi pi-clock text-gray-400"></i>
                {{ formatLastReading(sensor.last_reading) }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Vista de cards para móviles -->
    <div class="lg:hidden">
      <div class="grid gap-4 grid-cols-1 sm:grid-cols-2">
        <div
          v-for="sensor in sensors"
          :key="sensor.uid"
          class="border border-gray-200 rounded-xl p-4 bg-white transition-all shadow-sm hover:shadow-md"
          :class="{
            'border-l-4 border-l-green-500': sensor.status === 'online',
            'border-l-4 border-l-orange-500': sensor.status === 'warning',
            'border-l-4 border-l-red-500': sensor.status === 'offline'
          }"
        >
          <div class="flex justify-between items-center mb-4">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
                <i class="pi pi-microchip text-sm text-white"></i>
              </div>
              <code class="bg-gray-100 px-2 py-1 rounded-md text-xs font-mono font-semibold text-gray-700">{{ sensor.uid }}</code>
            </div>
            <div
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold"
              :class="{
                'bg-green-50 text-green-700 border border-green-200': sensor.status === 'online',
                'bg-orange-50 text-orange-700 border border-orange-200': sensor.status === 'warning',
                'bg-red-50 text-red-700 border border-red-200': sensor.status === 'offline'
              }"
            >
              <i class="pi pi-circle-fill text-[6px]"></i>
            </div>
          </div>

          <div class="mb-4 py-3 bg-gray-50 rounded-lg text-center">
            <div class="text-sm text-gray-600 uppercase tracking-wide mb-1">{{ sensor.last_value.type }}</div>
            <div>
              <span class="text-2xl font-bold text-gray-900">{{ sensor.last_value.value }}</span>
              <span class="text-sm text-gray-600 ml-1">{{ sensor.last_value.unit }}</span>
            </div>
          </div>

          <div class="flex justify-between text-xs text-gray-600">
            <div class="flex items-center gap-1.5">
              <i class="pi pi-clock text-gray-400"></i>
              {{ formatLastReading(sensor.last_reading) }}
            </div>
            <div class="flex items-center gap-1.5">
              <i class="pi pi-map-marker text-red-500"></i>
              {{ sensor.location }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
