<!-- Frontend/src/components/HistoricalChartGrid.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import IndividualChart from '@/components/IndividualChart.vue';

defineOptions({
  name: 'HistoricalChartGrid'
});

// Control de filtro global para los 4 gráficos
// Cargar desde localStorage o usar 1 hora por defecto
const savedTimeRange = localStorage.getItem('chartTimeRange');
const globalTimeRange = ref(savedTimeRange ? parseInt(savedTimeRange) : 1);

// Referencias a los 4 gráficos individuales
const temperatureChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);
const phChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);
const conductivityChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);
const waterLevelChartRef = ref<InstanceType<typeof IndividualChart> | null>(null);

// Variables para debouncing
let debounceTimer: ReturnType<typeof setTimeout> | null = null;
const isUpdating = ref(false);

/**
 * Updates the time range filter for all charts with debouncing
 * Para evitar demasiadas peticiones al hacer clics rápidos
 */
const handleTimeRangeChange = (hours: number) => {
  globalTimeRange.value = hours;
  // Guardar en localStorage inmediatamente para UX
  localStorage.setItem('chartTimeRange', hours.toString());

  // Limpiar timer anterior si existe
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  // Marcar que hay una actualización pendiente
  isUpdating.value = true;

  // Esperar 300ms después del último clic antes de actualizar
  debounceTimer = setTimeout(() => {
    temperatureChartRef.value?.updateTimeRange(hours);
    phChartRef.value?.updateTimeRange(hours);
    conductivityChartRef.value?.updateTimeRange(hours);
    waterLevelChartRef.value?.updateTimeRange(hours);
    isUpdating.value = false;
  }, 300);
};

/**
 * Refreshes data for all charts
 */
const refreshAllCharts = async () => {
  await Promise.all([
    temperatureChartRef.value?.refreshData(),
    phChartRef.value?.refreshData(),
    conductivityChartRef.value?.refreshData(),
    waterLevelChartRef.value?.refreshData()
  ]);
};

// Auto-refresh cada 30 segundos
setInterval(refreshAllCharts, 30000);

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
    <div class="flex justify-between items-center mb-6 pb-4 border-b-2 border-gray-100">
      <!-- Indicador de actualización -->
      <div class="flex items-center gap-2">
        <transition name="fade">
          <div v-if="isUpdating" class="flex items-center gap-2 text-blue-600 text-sm">
            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Actualizando gráficos...</span>
          </div>
        </transition>
      </div>
      
      <div class="flex items-center gap-4 flex-col md:flex-row">
        <label class="text-sm font-semibold text-gray-600">Período:</label>
        <div class="flex gap-2 bg-gray-100 rounded-lg p-1.5 flex-wrap">
          <button
            v-for="range in [
              { hours: 1, label: '1h' },
              { hours: 6, label: '6h' },
              { hours: 24, label: '24h' },
              { hours: 72, label: '3d' },
              { hours: 168, label: '7d' },
              { hours: 720, label: '30d' },
              { hours: 0, label: 'Todos' }
            ]"
            :key="range.hours"
            @click="handleTimeRangeChange(range.hours)"
            :class="globalTimeRange === range.hours ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'"
            class="px-4 py-2 rounded-lg cursor-pointer font-semibold transition-all text-sm min-w-[60px]"
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

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>