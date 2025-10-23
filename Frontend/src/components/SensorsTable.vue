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
  <div class="bg-white rounded-xl p-6 shadow-md">
    <!-- Header con botón actualizar -->
    <div class="flex justify-between items-center mb-6 pb-4 border-b-2 border-gray-100">
      <div class="flex gap-8">
        <div class="flex flex-col items-center gap-1">
          <span class="text-2xl font-bold text-success-500">{{ sensors.filter(s => s.status === 'online').length }}</span>
          <span class="text-xs text-gray-500 uppercase font-semibold">Conectados</span>
        </div>
        <div class="flex flex-col items-center gap-1">
          <span class="text-2xl font-bold text-warning-500">{{ sensors.filter(s => s.status === 'warning').length }}</span>
          <span class="text-xs text-gray-500 uppercase font-semibold">Advertencia</span>
        </div>
        <div class="flex flex-col items-center gap-1">
          <span class="text-2xl font-bold text-danger-500">{{ sensors.filter(s => s.status === 'offline').length }}</span>
          <span class="text-xs text-gray-500 uppercase font-semibold">Desconectados</span>
        </div>
      </div>
      <button
        @click="fetchSensorsStatus"
        class="flex items-center gap-2 px-4 py-2 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        :disabled="isLoading"
      >
        <i class="pi" :class="isLoading ? 'pi-spin pi-spinner' : 'pi-refresh'"></i>
        Actualizar
      </button>
    </div>

    <div v-if="error" class="flex items-center gap-2 p-4 bg-blue-50 rounded-md text-blue-700 mb-4">
      <i class="pi pi-info-circle"></i>
      <p>{{ error }}</p>
    </div>

    <div v-if="isLoading" class="flex items-center justify-center gap-2 py-12 text-gray-500">
      <i class="pi pi-spin pi-spinner"></i>
      Cargando estado de sensores...
    </div>

    <!-- Vista de tabla para desktop -->
    <div v-else class="hidden lg:block">
      <table class="w-full border-collapse">
        <thead>
          <tr class="bg-gray-100">
            <th class="text-left p-4 font-semibold text-gray-500 text-sm uppercase border-b-2 border-gray-200">UID Sensor (MAC)</th>
            <th class="text-left p-4 font-semibold text-gray-500 text-sm uppercase border-b-2 border-gray-200">Últimos Valores Registrados</th>
            <th class="text-left p-4 font-semibold text-gray-500 text-sm uppercase border-b-2 border-gray-200">Estado</th>
            <th class="text-left p-4 font-semibold text-gray-500 text-sm uppercase border-b-2 border-gray-200">Ubicación</th>
            <th class="text-left p-4 font-semibold text-gray-500 text-sm uppercase border-b-2 border-gray-200">Última Lectura</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sensor in sensors" :key="sensor.uid" class="hover:bg-primary-50 transition-colors">
            <!-- UID/MAC -->
            <td class="p-4 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <i class="pi pi-microchip text-primary-500"></i>
                <code class="bg-gray-100 px-2 py-1 rounded text-sm font-semibold font-mono">{{ sensor.uid }}</code>
              </div>
            </td>

            <!-- Últimos valores -->
            <td class="p-4 border-b border-gray-100 text-center">
              <div>
                <span class="text-2xl font-bold text-gray-800">{{ sensor.last_value.value }}</span>
                <span class="text-base text-gray-500 ml-1">{{ sensor.last_value.unit }}</span>
                <div class="text-xs text-gray-500 mt-1 uppercase font-medium">{{ sensor.last_value.type }}</div>
              </div>
            </td>

            <!-- Estado -->
            <td class="p-4 border-b border-gray-100">
              <div
                class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium"
                :class="{
                  'bg-success-100 text-success-500': sensor.status === 'online',
                  'bg-warning-100 text-warning-500': sensor.status === 'warning',
                  'bg-danger-100 text-danger-500': sensor.status === 'offline',
                  'bg-gray-100 text-gray-500': sensor.status !== 'online' && sensor.status !== 'warning' && sensor.status !== 'offline'
                }"
              >
                <i class="pi pi-circle-fill"></i>
                <span>{{ getStatusText(sensor.status) }}</span>
              </div>
              <div v-if="sensor.minutes_since_reading > 0" class="text-xs text-gray-500 mt-1">
                {{ sensor.minutes_since_reading }} min sin datos
              </div>
            </td>

            <!-- Ubicación -->
            <td class="p-4 border-b border-gray-100 text-gray-500">
              <i class="pi pi-map-marker text-danger-500 mr-2"></i>
              {{ sensor.location }}
            </td>

            <!-- Última lectura -->
            <td class="p-4 border-b border-gray-100 text-gray-500 text-sm">
              {{ formatLastReading(sensor.last_reading) }}
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
          class="border-2 border-gray-200 rounded-lg p-4 bg-white transition-all"
          :class="{
            'border-l-success-500': sensor.status === 'online',
            'border-l-warning-500': sensor.status === 'warning',
            'border-l-danger-500': sensor.status === 'offline'
          }"
        >
          <div class="flex justify-between items-center mb-4">
            <div class="flex items-center gap-2">
              <i class="pi pi-microchip"></i>
              <code class="bg-gray-100 px-2 py-1 rounded text-xs font-mono">{{ sensor.uid }}</code>
            </div>
            <div
              class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium"
              :class="{
                'bg-success-100 text-success-500': sensor.status === 'online',
                'bg-warning-100 text-warning-500': sensor.status === 'warning',
                'bg-danger-100 text-danger-500': sensor.status === 'offline'
              }"
            >
              <i class="pi pi-circle-fill"></i>
            </div>
          </div>

          <div class="mb-4">
            <div class="flex justify-between text-sm mb-2">
              <span>{{ sensor.last_value.type }}: <strong>{{ sensor.last_value.value }} {{ sensor.last_value.unit }}</strong></span>
            </div>
          </div>

          <div class="flex justify-between text-xs text-gray-500">
            <div class="flex items-center gap-1">
              <i class="pi pi-clock"></i>
              {{ formatLastReading(sensor.last_reading) }}
            </div>
            <div class="flex items-center gap-1">
              <i class="pi pi-map-marker"></i>
              {{ sensor.location }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
