<!-- Frontend/src/components/HistoricalChartGrid.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
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

// ========== RANGO DE FECHAS PERSONALIZADO ==========
const showCustomRange = ref(false);
const customStartDate = ref('');
const customEndDate = ref('');
const isCustomRangeActive = ref(false);

// Obtener fecha actual en formato YYYY-MM-DD para el máximo del datepicker
const today = computed(() => {
  const now = new Date();
  return now.toISOString().split('T')[0];
});

// Obtener fecha hace 1 año como mínimo sugerido
const oneYearAgo = computed(() => {
  const date = new Date();
  date.setFullYear(date.getFullYear() - 1);
  return date.toISOString().split('T')[0];
});

// Validar que las fechas sean correctas
const isCustomRangeValid = computed(() => {
  if (!customStartDate.value || !customEndDate.value) return false;
  return customStartDate.value <= customEndDate.value;
});

// Texto descriptivo del rango personalizado activo
const customRangeLabel = computed(() => {
  if (!isCustomRangeActive.value || !customStartDate.value || !customEndDate.value) return '';
  
  // Parsear las fechas manualmente para evitar problemas de zona horaria
  // El formato es YYYY-MM-DD
  const [startYear, startMonth, startDay] = customStartDate.value.split('-').map(Number);
  const [endYear, endMonth, endDay] = customEndDate.value.split('-').map(Number);
  
  const months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  
  const startLabel = `${startDay.toString().padStart(2, '0')}-${months[startMonth - 1]}`;
  const endLabel = `${endDay.toString().padStart(2, '0')}-${months[endMonth - 1]}`;
  
  return `${startLabel} - ${endLabel}`;
});

/**
 * Aplica el rango de fechas personalizado
 */
const applyCustomRange = () => {
  if (!isCustomRangeValid.value) return;
  
  isCustomRangeActive.value = true;
  globalTimeRange.value = -1; // -1 indica rango personalizado
  showCustomRange.value = false;
  
  // Guardar en localStorage
  localStorage.setItem('chartCustomStartDate', customStartDate.value);
  localStorage.setItem('chartCustomEndDate', customEndDate.value);
  localStorage.setItem('chartTimeRange', '-1');
  
  // Actualizar todos los gráficos con el rango personalizado
  updateChartsWithCustomRange();
};

/**
 * Actualiza los gráficos con el rango de fechas personalizado
 */
const updateChartsWithCustomRange = () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  isUpdating.value = true;
  
  debounceTimer = setTimeout(() => {
    temperatureChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value);
    phChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value);
    conductivityChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value);
    waterLevelChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value);
    isUpdating.value = false;
  }, 300);
};

/**
 * Limpia el rango personalizado y vuelve al modo normal
 */
const clearCustomRange = () => {
  isCustomRangeActive.value = false;
  customStartDate.value = '';
  customEndDate.value = '';
  showCustomRange.value = false;
  
  localStorage.removeItem('chartCustomStartDate');
  localStorage.removeItem('chartCustomEndDate');
  
  // Volver al rango por defecto (1 hora)
  handleTimeRangeChange(1);
};

// Cargar rango personalizado guardado al iniciar
onMounted(() => {
  const savedStart = localStorage.getItem('chartCustomStartDate');
  const savedEnd = localStorage.getItem('chartCustomEndDate');
  const savedRange = localStorage.getItem('chartTimeRange');
  
  if (savedRange === '-1' && savedStart && savedEnd) {
    customStartDate.value = savedStart;
    customEndDate.value = savedEnd;
    isCustomRangeActive.value = true;
    globalTimeRange.value = -1;
    
    // Esperar a que los gráficos estén montados y luego aplicar el rango
    setTimeout(() => {
      updateChartsWithCustomRange();
    }, 500);
  }
});

/**
 * Updates the time range filter for all charts with debouncing
 * Para evitar demasiadas peticiones al hacer clics rápidos
 */
const handleTimeRangeChange = (hours: number) => {
  // Desactivar rango personalizado al seleccionar un preset
  isCustomRangeActive.value = false;
  customStartDate.value = '';
  customEndDate.value = '';
  localStorage.removeItem('chartCustomStartDate');
  localStorage.removeItem('chartCustomEndDate');
  
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
 * Respeta el modo de rango personalizado
 */
const refreshAllCharts = async () => {
  // Si hay un rango personalizado activo, refrescar con ese rango
  if (isCustomRangeActive.value && customStartDate.value && customEndDate.value) {
    await Promise.all([
      temperatureChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value),
      phChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value),
      conductivityChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value),
      waterLevelChartRef.value?.updateCustomDateRange(customStartDate.value, customEndDate.value)
    ]);
  } else {
    // Modo normal: refrescar con el rango de horas
    await Promise.all([
      temperatureChartRef.value?.refreshData(),
      phChartRef.value?.refreshData(),
      conductivityChartRef.value?.refreshData(),
      waterLevelChartRef.value?.refreshData()
    ]);
  }
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
        
        <!-- Badge de rango personalizado activo -->
        <div v-if="isCustomRangeActive" class="flex items-center gap-2 bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg text-sm font-medium">
          <i class="pi pi-calendar"></i>
          <span>{{ customRangeLabel }}</span>
          <button 
            @click="clearCustomRange" 
            class="ml-1 hover:bg-blue-200 rounded p-0.5 transition-colors"
            title="Limpiar rango"
          >
            <i class="pi pi-times text-xs"></i>
          </button>
        </div>
      </div>
      
      <div class="flex items-center gap-4 flex-col md:flex-row">
        <label class="text-sm font-semibold text-gray-600">Período:</label>
        <div class="flex gap-2 bg-gray-100 rounded-lg p-1.5 flex-wrap items-center">
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
            :class="globalTimeRange === range.hours && !isCustomRangeActive ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'"
            class="px-4 py-2 rounded-lg cursor-pointer font-semibold transition-all text-sm min-w-[60px]"
          >
            {{ range.label }}
          </button>
          
          <!-- Separador -->
          <div class="w-px h-8 bg-gray-300 mx-1"></div>
          
          <!-- Botón de rango personalizado -->
          <button
            @click="showCustomRange = !showCustomRange"
            :class="isCustomRangeActive ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md' : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'"
            class="px-4 py-2 rounded-lg cursor-pointer font-semibold transition-all text-sm flex items-center gap-2"
            title="Seleccionar rango de fechas personalizado"
          >
            <i class="pi pi-calendar"></i>
            <span class="hidden sm:inline">Personalizado</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Panel de selección de rango personalizado -->
    <transition name="slide-fade">
      <div v-if="showCustomRange" class="mb-6 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-200">
        <div class="flex flex-col md:flex-row items-start md:items-end gap-4">
          <div class="flex-1">
            <label class="block text-sm font-semibold text-gray-700 mb-2">
              <i class="pi pi-calendar-plus mr-1"></i>
              Fecha inicio
            </label>
            <input
              v-model="customStartDate"
              type="date"
              :max="customEndDate || today"
              :min="oneYearAgo"
              class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-800 transition-all"
            />
          </div>
          
          <div class="flex items-center justify-center py-2">
            <i class="pi pi-arrow-right text-gray-400 text-xl"></i>
          </div>
          
          <div class="flex-1">
            <label class="block text-sm font-semibold text-gray-700 mb-2">
              <i class="pi pi-calendar mr-1"></i>
              Fecha fin
            </label>
            <input
              v-model="customEndDate"
              type="date"
              :min="customStartDate || oneYearAgo"
              :max="today"
              class="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-800 transition-all"
            />
          </div>
          
          <div class="flex gap-2">
            <button
              @click="applyCustomRange"
              :disabled="!isCustomRangeValid"
              class="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg font-semibold transition-all hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-md"
            >
              <i class="pi pi-check"></i>
              Aplicar
            </button>
            <button
              @click="showCustomRange = false"
              class="px-4 py-2.5 bg-gray-200 text-gray-700 rounded-lg font-semibold transition-all hover:bg-gray-300"
            >
              <i class="pi pi-times"></i>
            </button>
          </div>
        </div>
        
        <!-- Mensaje de ayuda -->
        <p class="mt-3 text-xs text-indigo-600 flex items-center gap-1">
          <i class="pi pi-info-circle"></i>
          Selecciona un rango de fechas para ver los datos históricos de ese período específico.
        </p>
      </div>
    </transition>

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

.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>