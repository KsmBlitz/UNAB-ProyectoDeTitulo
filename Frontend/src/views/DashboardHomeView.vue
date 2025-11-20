<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { themeStore } from '@/stores/themeStore';
// Store para modo oscuro/claro
// themeStore es reactivo por diseño
import MetricCard from '@/components/MetricCard.vue';
import SensorsTable from '@/components/SensorsTable.vue';
import HistoricalChartGrid from '@/components/HistoricalChartGrid.vue';
import { API_BASE_URL } from '@/config/api';
import { evaluateMetricStatus, BLUEBERRY_THRESHOLDS } from '@/utils/metrics';

defineOptions({
  name: 'DashboardHomeView'
});

interface MetricData {
  value: number;
  unit: string;
  changeText: string;
  isPositive: boolean;
  status: 'optimal' | 'warning' | 'critical';
}

interface Metrics {
  temperatura_agua: MetricData;
  ph: MetricData;
  conductividad: MetricData;
  nivel_agua: MetricData;
}

// Estados para métricas
const metrics = ref<Metrics | null>(null);
const errorMetrics = ref<string | null>(null);
const isLoadingMetrics = ref(true);

// Referencias a componentes hijos
const sensorsTableRef = ref<InstanceType<typeof SensorsTable> | null>(null);
const chartsGridRef = ref<InstanceType<typeof HistoricalChartGrid> | null>(null);


onMounted(async () => {
  themeStore.applyTheme();
  await fetchMetrics();
  
  // Auto-refresh cada 30 segundos
  setInterval(fetchMetrics, 30000);
});

watch(() => themeStore.isDark, () => {
  themeStore.applyTheme();
});

async function fetchMetrics() {
  // Solo mostrar loading en la primera carga
  if (!metrics.value) {
    isLoadingMetrics.value = true;
  }

  errorMetrics.value = null;

  const token = localStorage.getItem('userToken');

  if (!token) {
    errorMetrics.value = "Error de autenticación. Por favor, inicia sesión nuevamente.";
    isLoadingMetrics.value = false;
    return;
  }

  try {
  
    const response = await fetch(`${API_BASE_URL}/api/metrics/latest`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('No hay mediciones disponibles en este momento.');
      } else if (response.status === 401) {
        throw new Error('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
      } else {
        throw new Error(`Error del servidor (${response.status}). Las mediciones pueden tardar hasta 5 minutos en actualizarse.`);
      }
    }

    const rawData = await response.json();
    
    // Transform backend format to frontend format
    const temperatura = rawData.temperature ?? 0;
    const ph = rawData.ph ?? 0;
    const conductividad = rawData.conductivity ?? 0;
    const nivel = rawData.water_level ?? 0;
    
    // Helper to map 'normal' to 'optimal'
    const mapStatus = (status: 'normal' | 'warning' | 'critical'): 'optimal' | 'warning' | 'critical' => {
      return status === 'normal' ? 'optimal' : status;
    };
    
    metrics.value = {
      temperatura_agua: {
        value: temperatura,
        unit: '°C',
        changeText: temperatura > 0 ? 'Actualizado' : 'Sin datos',
        isPositive: temperatura >= BLUEBERRY_THRESHOLDS.temperature.optimal_min && temperatura <= BLUEBERRY_THRESHOLDS.temperature.optimal_max,
        status: mapStatus(evaluateMetricStatus(temperatura, BLUEBERRY_THRESHOLDS.temperature))
      },
      ph: {
        value: ph,
        unit: '',
        changeText: ph > 0 ? 'Actualizado' : 'Sin datos',
        isPositive: ph >= BLUEBERRY_THRESHOLDS.ph.optimal_min && ph <= BLUEBERRY_THRESHOLDS.ph.optimal_max,
        status: mapStatus(evaluateMetricStatus(ph, BLUEBERRY_THRESHOLDS.ph))
      },
      conductividad: {
        value: conductividad,
        unit: 'mS/cm',
        changeText: conductividad > 0 ? 'Actualizado' : 'Sin datos',
        isPositive: conductividad <= BLUEBERRY_THRESHOLDS.conductivity.optimal_max,
        status: mapStatus(evaluateMetricStatus(conductividad, BLUEBERRY_THRESHOLDS.conductivity))
      },
      nivel_agua: {
        value: nivel,
        unit: 'cm',
        changeText: nivel > 0 ? 'Actualizado' : 'Sin datos',
        isPositive: nivel >= BLUEBERRY_THRESHOLDS.water_level.optimal_min && nivel <= BLUEBERRY_THRESHOLDS.water_level.optimal_max,
        status: mapStatus(evaluateMetricStatus(nivel, BLUEBERRY_THRESHOLDS.water_level))
      }
    };
  } catch (e) {
    console.error('Error al cargar métricas:', e);
    if (e instanceof Error) {
      errorMetrics.value = e.message;
    } else {
      errorMetrics.value = "Error al cargar las métricas. Intenta actualizar la página.";
    }
  } finally {
    isLoadingMetrics.value = false;
  }
}
</script>

<template>
  <!-- Fondo dependiente del modo (igual que login) -->
  <div
    class="min-h-screen p-8 transition-colors duration-300 bg-gradient-to-br from-white via-blue-100 to-blue-200"
  >
    <!-- Header mejorado -->
    <header class="mb-10">
  <div class="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
        <div class="flex items-center gap-4 mb-3">
          <div class="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
            <i class="pi pi-chart-line text-2xl text-white"></i>
          </div>
          <div>
            <h1 class="text-3xl font-bold text-gray-800 mb-1">Monitoreo del Embalse</h1>
            <p class="text-gray-600 text-base">Sistema de control de calidad del agua</p>
          </div>
        </div>
      </div>
    </header>

    <!-- 1. Métricas principales (Cards) -->
    <section class="mb-10">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
          <i class="pi pi-gauge text-white text-lg"></i>
        </div>
  <h2 class="text-2xl font-bold text-gray-800">Últimas Mediciones</h2>
      </div>

      <!-- Error Message -->
  <div v-if="errorMetrics" class="flex items-start gap-4 p-6 bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-300 rounded-xl text-orange-800 shadow-md">
        <div class="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center flex-shrink-0">
          <i class="pi pi-exclamation-triangle text-xl text-white"></i>
        </div>
        <div class="flex-1">
          <p class="font-semibold mb-2">Error al cargar datos</p>
          <p class="text-sm">{{ errorMetrics }}</p>
        </div>
        <button @click="fetchMetrics" class="px-5 py-2.5 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors duration-200 font-semibold shadow-md hover:shadow-lg flex items-center gap-2 flex-shrink-0">
          <i class="pi pi-refresh"></i>
          Reintentar
        </button>
      </div>

      <!-- Loading State -->
      <div v-else-if="isLoadingMetrics" class="py-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="i in 4" :key="i" class="h-36 rounded-xl overflow-hidden relative bg-gray-100">
            <div class="absolute inset-0 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 animate-pulse"></div>
          </div>
        </div>
      </div>

      <!-- Metrics Grid -->
      <div v-else-if="metrics" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

        <MetricCard
          title="Temperatura del Agua"
          :value="metrics.temperatura_agua?.value ? metrics.temperatura_agua.value.toFixed(1) : 'N/A'"
          :unit="metrics.temperatura_agua?.unit ?? '°C'"
          :changeText="metrics.temperatura_agua?.changeText ?? 'Sin datos'"
          :isPositive="metrics.temperatura_agua?.isPositive ?? false"
          :status="metrics.temperatura_agua?.status ?? 'critical'"
          icon="pi pi-sun"
        />


        <MetricCard
          title="Nivel de pH"
          :value="metrics.ph?.value ? metrics.ph.value.toFixed(1) : 'N/A'"
          :unit="metrics.ph?.unit ?? ''"
          :changeText="metrics.ph?.changeText ?? 'Sin datos'"
          :isPositive="metrics.ph?.isPositive ?? false"
          :status="metrics.ph?.status ?? 'critical'"
          icon="pi pi-flask"
        />


        <MetricCard
          title="Conductividad Eléctrica"
          :value="metrics.conductividad?.value ? metrics.conductividad.value.toFixed(1) : 'N/A'"
          :unit="metrics.conductividad?.unit ?? 'mS/cm'"
          :changeText="metrics.conductividad?.changeText ?? 'Sin datos'"
          :isPositive="metrics.conductividad?.isPositive ?? false"
          :status="metrics.conductividad?.status ?? 'critical'"
          icon="pi pi-bolt"
        />


        <!-- Nivel del Agua: mostrar como no disponible / Próximamente y en gris -->
        <div class="opacity-80 bg-gray-50 rounded-xl p-0 border border-gray-200">
          <MetricCard
            title="Nivel del Agua"
            :value="'Próximamente'"
            :unit="''"
            :changeText="'Próximamente'"
            :isPositive="false"
            :status="undefined"
            icon="pi pi-chart-bar"
          />
        </div>
      </div>

      <div v-else class="flex items-start gap-4 p-6 bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-300 rounded-xl text-blue-800 shadow-md">
        <div class="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center flex-shrink-0">
          <i class="pi pi-info-circle text-xl text-white"></i>
        </div>
        <div class="flex-1">
          <p class="font-semibold mb-2">No hay datos disponibles</p>
          <p class="text-sm">Esperando lecturas de los sensores...</p>
        </div>
      </div>

      <!-- Leyenda de colores -->
  <div v-if="metrics" class="mt-8 p-6 bg-white border-2 border-blue-200 rounded-xl shadow-md">
        <div class="flex items-center gap-3 mb-5">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-md">
            <i class="pi pi-info-circle text-white text-base"></i>
          </div>
          <h3 class="text-lg font-normal text-gray-800 m-0">
            Valores Ideales Para el Cultivo de Arándanos
          </h3>
        </div>
        <div class="flex flex-wrap gap-8">
          <div class="flex items-center gap-3">
            <div class="w-6 h-6 rounded-lg border-2 border-green-500 bg-green-100 flex-shrink-0 shadow-sm"></div>
            <span class="font-semibold text-gray-700">Óptimo</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-6 h-6 rounded-lg border-2 border-orange-500 bg-orange-100 flex-shrink-0 shadow-sm"></div>
            <span class="font-semibold text-gray-700">Advertencia</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-6 h-6 rounded-lg border-2 border-red-500 bg-red-100 flex-shrink-0 shadow-sm"></div>
            <span class="font-semibold text-gray-700">Crítico</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 2. Grid de gráficos históricos (4 gráficos) -->
    <section class="mb-10">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
          <i class="pi pi-chart-line text-white text-lg"></i>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">Tendencia Histórica por Parámetro</h2>
      </div>
      <HistoricalChartGrid ref="chartsGridRef" />
    </section>

    <!-- 3. Tabla de sensores detallada -->
    <section class="mb-10">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg">
          <i class="pi pi-microchip text-white text-lg"></i>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">Estado de Sensores IoT</h2>
      </div>
      <SensorsTable ref="sensorsTableRef" />
    </section>
  </div>
</template>

