<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { API_BASE_URL } from '@/config/api';

defineOptions({
  name: 'SensorsTable'
});

interface SensorReading {
  uid: string;
  last_values: {
    temperature: number;
    ph: number;
    ec: number;
    water_level: number;
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
  // Solo mostrar loading en la primera carga
  if (sensors.value.length === 0) {
    isLoading.value = true;
  }
  
  error.value = null;

  const token = localStorage.getItem('userToken');

  if (!token) {
    error.value = 'No hay token de autenticación';
    isLoading.value = false;
    return;
  }

  try {
  
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

    // Siempre actualizar, pero sin mostrar loading después de la primera carga
    sensors.value = sensorsData.map((sensor: any) => ({
      uid: sensor.uid || 'N/A',
      last_values: sensor.last_values || {
        temperature: 0,
        ph: 0,
        ec: 0,
        water_level: 0
      },
      status: sensor.status || 'offline',
      location: sensor.location || 'Desconocida',
      last_reading: sensor.last_reading || new Date().toISOString(),
      minutes_since_reading: sensor.minutes_since_reading || 0
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
  // Formatear en hora local de Chile (UTC-3)
  return date.toLocaleDateString('es-CL', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'America/Santiago'
  });
};

// Función para obtener calidad de señal basada en minutos desde última lectura
const getSignalQuality = (minutes: number) => {
  if (minutes < 5) {
    return { level: 'Excelente', icon: 'pi pi-wifi', color: 'text-green-600', bg: 'bg-green-100', bars: 4 };
  } else if (minutes < 15) {
    return { level: 'Buena', icon: 'pi pi-wifi', color: 'text-blue-600', bg: 'bg-blue-100', bars: 3 };
  } else if (minutes < 30) {
    return { level: 'Regular', icon: 'pi pi-wifi', color: 'text-yellow-600', bg: 'bg-yellow-100', bars: 2 };
  } else if (minutes < 60) {
    return { level: 'Débil', icon: 'pi pi-wifi', color: 'text-orange-600', bg: 'bg-orange-100', bars: 1 };
  } else {
    return { level: 'Sin Señal', icon: 'pi pi-times-circle', color: 'text-red-600', bg: 'bg-red-100', bars: 0 };
  }
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
</script>

<template>
  <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
    <!-- Header sin botón actualizar -->
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
      <!-- Indicador de actualización automática -->
      <div class="flex items-center gap-2 text-sm text-gray-500">
        <i class="pi pi-sync text-xs" :class="{ 'pi-spin': isLoading }"></i>
        <span>Actualización automática cada 30s</span>
      </div>
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
            <th class="text-left p-4 font-semibold text-gray-700 text-xs uppercase tracking-wider border-b border-gray-300">Calidad de Señal</th>
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

            <!-- Calidad de Señal -->
            <td class="p-4 border-b border-gray-100">
              <div class="flex items-center gap-3">
                <!-- Indicador visual de barras de señal -->
                <div class="flex items-end gap-0.5 h-8">
                  <div 
                    v-for="bar in 4" 
                    :key="bar"
                    class="w-1.5 rounded-t transition-all"
                    :class="bar <= getSignalQuality(sensor.minutes_since_reading).bars 
                      ? getSignalQuality(sensor.minutes_since_reading).bg.replace('bg-', 'bg-') + ' opacity-100'
                      : 'bg-gray-200 opacity-40'"
                    :style="{ height: `${bar * 25}%` }"
                  ></div>
                </div>
                
                <!-- Texto de calidad -->
                <div>
                  <div class="flex items-center gap-1.5">
                    <span 
                      class="font-semibold text-sm"
                      :class="getSignalQuality(sensor.minutes_since_reading).color"
                    >
                      {{ getSignalQuality(sensor.minutes_since_reading).level }}
                    </span>
                  </div>
                  <div class="text-xs text-gray-500 mt-0.5">
                    Hace {{ sensor.minutes_since_reading }} min
                  </div>
                </div>
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

          <!-- Calidad de Señal en Mobile -->
          <div class="mb-4 py-4 bg-gray-50 rounded-lg">
            <div class="flex flex-col items-center gap-3">
              <div class="text-xs font-medium text-gray-500 uppercase tracking-wide">Calidad de Señal</div>
              
              <!-- Signal bars -->
              <div class="flex items-end gap-1 h-12">
                <div v-for="bar in 4" :key="bar"
                  class="w-2.5 rounded-t transition-all"
                  :class="bar <= getSignalQuality(sensor.minutes_since_reading).bars 
                    ? getSignalQuality(sensor.minutes_since_reading).bg + ' opacity-100'
                    : 'bg-gray-200 opacity-40'"
                  :style="{ height: `${bar * 25}%` }">
                </div>
              </div>
              
              <!-- Quality text -->
              <div class="flex items-center gap-2">
                <span class="font-bold text-base"
                      :class="getSignalQuality(sensor.minutes_since_reading).color">
                  {{ getSignalQuality(sensor.minutes_since_reading).level }}
                </span>
              </div>
              
              <!-- Time indicator -->
              <div class="text-sm text-gray-500">
                Hace {{ sensor.minutes_since_reading }} min
              </div>
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
