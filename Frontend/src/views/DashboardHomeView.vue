<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import MetricCard from '@/components/MetricCard.vue';
import SensorsTable from '@/components/SensorsTable.vue';
import HistoricalChartGrid from '@/components/HistoricalChartGrid.vue';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

defineOptions({
  name: 'DashboardHomeView'
});

interface MetricData {
  value: number;
  unit: string;
  changeText: string;
  isPositive: boolean;
  status: 'normal' | 'warning' | 'critical';
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
  await fetchMetrics();
});

async function fetchMetrics() {
  // No cambiar isLoadingMetrics si ya hay datos (para evitar parpadeo)
  const shouldShowLoading = !metrics.value;
  if (shouldShowLoading) {
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
    // ✅ CAMBIAR URL
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

    metrics.value = await response.json();
  } catch (e) {
    console.error('Error al cargar métricas:', e);
    if (e instanceof Error) {
      errorMetrics.value = e.message;
    } else {
      errorMetrics.value = "Error al cargar las métricas. Intenta actualizar la página.";
    }
  } finally {
    if (shouldShowLoading) {
      isLoadingMetrics.value = false;
    }
  }
}
</script>

<template>
  <div class="p-6 max-w-[1400px] mx-auto">
    <!-- Header simplificado -->
    <header class="flex justify-between items-center mb-8 pb-4 border-b-2 border-gray-100">
      <div>
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Monitoreo del Embalse</h1>
        <p class="text-gray-600 text-lg">Sistema de control de calidad del agua</p>
      </div>
    </header>

    <!-- 1. Métricas principales (Cards) -->
    <section class="mb-8">
      <h2 class="section-title">
        <i class="pi pi-gauge text-primary-500"></i>
        Últimas Mediciones
      </h2>

      <!-- Error Message -->
      <div v-if="errorMetrics" class="flex items-center gap-3 p-6 bg-warning-100 border border-warning-300 rounded-lg text-warning-800">
        <i class="pi pi-exclamation-triangle text-xl"></i>
        {{ errorMetrics }}
        <button @click="fetchMetrics" class="btn btn-primary ml-auto">Reintentar</button>
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
          :value="String(metrics.temperatura_agua.value)"
          :unit="metrics.temperatura_agua.unit"
          :changeText="metrics.temperatura_agua.changeText"
          :isPositive="metrics.temperatura_agua.isPositive"
          :status="metrics.temperatura_agua.status"
          icon="pi pi-sun"
        />

        <MetricCard
          title="Nivel de pH"
          :value="String(metrics.ph.value)"
          :unit="metrics.ph.unit"
          :changeText="metrics.ph.changeText"
          :isPositive="metrics.ph.isPositive"
          :status="metrics.ph.status"
          icon="pi pi-flask"
        />

        <MetricCard
          title="Conductividad Eléctrica"
          :value="String(metrics.conductividad.value)"
          :unit="metrics.conductividad.unit"
          :changeText="metrics.conductividad.changeText"
          :isPositive="metrics.conductividad.isPositive"
          :status="metrics.conductividad.status"
          icon="pi pi-bolt"
        />

        <MetricCard
          title="Nivel del Agua"
          :value="String(metrics.nivel_agua.value)"
          :unit="metrics.nivel_agua.unit"
          :changeText="metrics.nivel_agua.changeText"
          :isPositive="metrics.nivel_agua.isPositive"
          :status="metrics.nivel_agua.status"
          icon="pi pi-chart-bar"
        />
      </div>

      <!-- Leyenda de colores -->
      <div v-if="metrics" class="mt-6 p-5 bg-gray-50 border border-gray-200 rounded-xl">
        <h3 class="flex items-center gap-2 text-base font-semibold text-gray-700 mb-4">
          <i class="pi pi-info-circle text-gray-600 text-sm"></i>
          Valores ideales para arándanos
        </h3>
        <div class="flex flex-wrap gap-6">
          <div class="flex items-center gap-3 text-sm text-gray-700">
            <div class="w-5 h-5 rounded border-2 border-success-500 bg-success-100 flex-shrink-0"></div>
            <span>Óptimo</span>
          </div>
          <div class="flex items-center gap-3 text-sm text-gray-700">
            <div class="w-5 h-5 rounded border-2 border-warning-500 bg-warning-100 flex-shrink-0"></div>
            <span>Advertencia</span>
          </div>
          <div class="flex items-center gap-3 text-sm text-gray-700">
            <div class="w-5 h-5 rounded border-2 border-danger-500 bg-danger-100 flex-shrink-0"></div>
            <span>Crítico</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 2. Grid de gráficos históricos (4 gráficos) -->
    <section class="mb-8">
      <h2 class="section-title">
        <i class="pi pi-chart-line text-primary-500"></i>
        Tendencia Histórica por Parámetro
      </h2>
      <HistoricalChartGrid ref="chartsGridRef" />
    </section>

    <!-- 3. Tabla de sensores detallada -->
    <section class="mb-8">
      <h2 class="section-title">
        <i class="pi pi-microchip text-primary-500"></i>
        Estado de Sensores IoT
      </h2>
      <SensorsTable ref="sensorsTableRef" />
    </section>
  </div>
</template>

<!-- Todos los estilos ahora son manejados por Tailwind CSS -->
