<!-- Frontend/src/components/HistoricalChartGrid.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import IndividualChart from '@/components/IndividualChart.vue';

defineOptions({
  name: 'HistoricalChartGrid'
});

// Control de filtro global para los 4 gráficos
const globalTimeRange = ref(24); // horas por defecto

// Referencias a los 4 gráficos individuales
const temperatureChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);
const phChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);
const conductivityChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);
const waterLevelChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);

// Función para cambiar el filtro temporal de todos los gráficos
const handleTimeRangeChange = (hours: number) => {
  globalTimeRange.value = hours;

  // Actualizar todos los gráficos con el nuevo filtro
  temperatureChartRef.value?.updateTimeRange(hours);
  phChartRef.value?.updateTimeRange(hours);
  conductivityChartRef.value?.updateTimeRange(hours);
  waterLevelChartRef.value?.updateTimeRange(hours);
};

// Función para refrescar todos los gráficos (llamada desde el padre)
const refreshAllCharts = async () => {
  await Promise.all([
    temperatureChartRef.value?.refreshData(),
    phChartRef.value?.refreshData(),
    conductivityChartRef.value?.refreshData(),
    waterLevelChartRef.value?.refreshData()
  ]);
};

// Exponer funciones al componente padre
defineExpose({
  refreshAllCharts
});

onMounted(() => {
  // Los gráficos individuales se inicializarán automáticamente
});
</script>

<template>
  <div class="bg-white rounded-xl p-6 shadow-md">
    <!-- Controles de filtro temporal (compartidos por todos los gráficos) -->
    <div class="flex justify-end mb-6 pb-4 border-b-2 border-gray-100">
      <div class="flex items-center gap-4 flex-col md:flex-row">
        <label class="text-sm font-semibold text-gray-500">Período:</label>
        <div class="flex gap-1 bg-gray-100 rounded-md p-1 flex-wrap">
          <button
            v-for="range in [
              { hours: 1, label: '1h' },
              { hours: 6, label: '6h' },
              { hours: 24, label: '24h' },
              { hours: 168, label: '7d' },
              { hours: 720, label: '30d' },
              { hours: 8760, label: '1 año' },
              { hours: 0, label: 'Todo' }
            ]"
            :key="range.hours"
            @click="handleTimeRangeChange(range.hours)"
            :class="globalTimeRange === range.hours ? 'bg-primary-500 text-white' : 'bg-transparent hover:bg-gray-200'"
            class="px-4 py-2 rounded border-none cursor-pointer font-medium transition-all text-sm min-w-[60px]"
          >
            {{ range.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Grid 2x2 de gráficos individuales -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <!-- Fila superior -->
      <div class="bg-gray-50 rounded-lg overflow-hidden border border-gray-200 transition-all hover:-translate-y-0.5 hover:shadow-lg h-[350px]">
        <IndividualChart
          ref="temperatureChartRef"
          sensor-type="temperatura"
          title="Temperatura del Agua"
          :time-range="globalTimeRange"
          color="#f39c12"
          icon="pi pi-sun"
          unit="°C"
        />
      </div>

      <div class="bg-gray-50 rounded-lg overflow-hidden border border-gray-200 transition-all hover:-translate-y-0.5 hover:shadow-lg h-[350px]">
        <IndividualChart
          ref="phChartRef"
          sensor-type="ph"
          title="Nivel de pH"
          :time-range="globalTimeRange"
          color="#e74c3c"
          icon="pi pi-flask"
          unit=""
        />
      </div>

      <!-- Fila inferior -->
      <div class="bg-gray-50 rounded-lg overflow-hidden border border-gray-200 transition-all hover:-translate-y-0.5 hover:shadow-lg h-[350px]">
        <IndividualChart
          ref="conductivityChartRef"
          sensor-type="conductividad"
          title="Conductividad Eléctrica"
          :time-range="globalTimeRange"
          color="#9b59b6"
          icon="pi pi-bolt"
          unit="dS/m"
        />
      </div>

      <div class="bg-gray-50 rounded-lg overflow-hidden border border-gray-200 transition-all hover:-translate-y-0.5 hover:shadow-lg h-[350px]">
        <IndividualChart
          ref="waterLevelChartRef"
          sensor-type="nivel"
          title="Nivel del Agua"
          :time-range="globalTimeRange"
          color="#3498db"
          icon="pi pi-chart-bar"
          unit="m"
        />
      </div>
    </div>
  </div>
</template>
