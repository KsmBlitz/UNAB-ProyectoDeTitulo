<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useApi } from '@/composables/useApi';
import { notify } from '@/stores/notificationStore';

defineOptions({
  name: 'AnalyticsView'
});

// Estados
const isLoading = ref(false);
const selectedPeriod = ref<'week' | 'month' | 'quarter'>('month');
const correlationData = ref<any>(null);
const anomalies = ref<any[]>([]);
const predictions = ref<any>(null);

// Paginación de anomalías
const anomaliesPage = ref(1);
const anomaliesPerPage = 10;

// Datos para comparativa
const currentPeriodStats = ref<any>(null);
const previousPeriodStats = ref<any>(null);

// Configuración de correlación - use correct field names
const correlationVars = ref({
  var1: 'pH',
  var2: 'temperature'
});

// Opciones de variables - use correct field names matching backend
const availableVars = [
  { label: 'pH', value: 'pH' },
  { label: 'Temperatura', value: 'temperature' },
  { label: 'Electroconductividad', value: 'EC' }
];

// Mapeo de nombres técnicos a español
const getVariableLabel = (varName: string): string => {
  const labels: Record<string, string> = {
    'pH': 'pH',
    'temperature': 'Temperatura',
    'Temperature': 'Temperatura',
    'EC': 'Electroconductividad',
    'pH_Value': 'pH'
  };
  return labels[varName] || varName;
};

// Composable API
const api = useApi();

// Computed
const periodLabel = computed(() => {
  const labels = {
    week: 'Última Semana',
    month: 'Último Mes',
    quarter: 'Último Trimestre'
  };
  return labels[selectedPeriod.value];
});

const correlationCoefficient = computed(() => {
  if (!correlationData.value) return null;
  return correlationData.value.coefficient?.toFixed(3);
});

const correlationStrength = computed(() => {
  const coef = Math.abs(parseFloat(correlationCoefficient.value || '0'));
  if (coef >= 0.7) return { label: 'Fuerte', color: 'text-green-600' };
  if (coef >= 0.4) return { label: 'Moderada', color: 'text-yellow-600' };
  return { label: 'Débil', color: 'text-gray-600' };
});

const growthPercentage = computed(() => {
  if (!currentPeriodStats.value || !previousPeriodStats.value) return null;
  
  const current = currentPeriodStats.value.avgPH || 0;
  const previous = previousPeriodStats.value.avgPH || 0;
  
  if (previous === 0) return 0;
  
  return (((current - previous) / previous) * 100).toFixed(2);
});

// Computed para paginación de anomalías
const totalAnomaliesPages = computed(() => {
  return Math.ceil(anomalies.value.length / anomaliesPerPage);
});

const paginatedAnomalies = computed(() => {
  const start = (anomaliesPage.value - 1) * anomaliesPerPage;
  const end = start + anomaliesPerPage;
  return anomalies.value.slice(start, end);
});

// Métodos
const fetchAnalyticsData = async () => {
  isLoading.value = true;
  anomaliesPage.value = 1; // Reset page when fetching new data
  try {
    // 1. Calcular correlación
    await calculateCorrelation();
    
    // 2. Detectar anomalías
    await detectAnomalies();
    
    // 3. Comparativa histórica
    await fetchHistoricalComparison();
    
  } catch (error: any) {
    console.error('Error fetching analytics:', error);
    notify.error(error.message || 'Error al cargar datos de analítica');
  } finally {
    isLoading.value = false;
  }
};

const calculateCorrelation = async () => {
  try {
    const response: any = await api.post('/api/analytics/correlation', {
      variable1: correlationVars.value.var1,
      variable2: correlationVars.value.var2,
      period: selectedPeriod.value
    });
    
    correlationData.value = response;
  } catch (error: any) {
    console.error('Error calculating correlation:', error);
    correlationData.value = null;
    notify.error('Error al calcular correlación');
  }
};

const detectAnomalies = async () => {
  try {
    const response: any = await api.get('/api/analytics/anomalies', {
      params: { period: selectedPeriod.value }
    });
    
    anomalies.value = response.anomalies || [];
  } catch (error: any) {
    console.error('Error detecting anomalies:', error);
    anomalies.value = [];
    notify.error('Error al detectar anomalías');
  }
};

const fetchPredictions = async () => {
  try {
    const response: any = await api.get('/api/analytics/predictions', {
      params: { hours: 48 }
    });
    
    predictions.value = response;
  } catch (error: any) {
    console.error('Error fetching predictions:', error);
    predictions.value = null;
  }
};

const fetchHistoricalComparison = async () => {
  try {
    const response: any = await api.get('/api/analytics/comparison', {
      params: { period: selectedPeriod.value }
    });
    
    currentPeriodStats.value = response.current;
    previousPeriodStats.value = response.previous;
  } catch (error: any) {
    console.error('Error fetching historical comparison:', error);
    currentPeriodStats.value = null;
    previousPeriodStats.value = null;
    notify.error('Error al cargar comparativa histórica');
  }
};

const exportToPDF = async () => {
  try {
    notify.info('Generando reporte PDF...');
    
    const response: any = await api.get('/api/analytics/export/pdf', {
      params: { period: selectedPeriod.value },
      responseType: 'blob'
    });
    
    // Crear un enlace de descarga
    const url = window.URL.createObjectURL(new Blob([response]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `reporte-analitica-${Date.now()}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    notify.success('Reporte PDF descargado exitosamente');
  } catch (error: any) {
    console.error('Error exporting PDF:', error);
    notify.error('Error al generar el reporte PDF');
  }
};

const exportToExcel = async () => {
  try {
    notify.info('Generando reporte Excel...');
    
    const response: any = await api.get('/api/analytics/export/excel', {
      params: { period: selectedPeriod.value },
      responseType: 'blob'
    });
    
    // Crear un enlace de descarga
    const url = window.URL.createObjectURL(new Blob([response]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `reporte-analitica-${Date.now()}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    notify.success('Reporte Excel descargado exitosamente');
  } catch (error: any) {
    console.error('Error exporting Excel:', error);
    notify.error('Error al generar el reporte Excel');
  }
};

const refreshData = () => {
  fetchAnalyticsData();
};

// Helper functions
const formatNumber = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  return value.toFixed(decimals);
};

const parseFloatSafe = (value: any): number => {
  const parsed = parseFloat(value);
  return isNaN(parsed) ? 0 : parsed;
};

const formatDateTime = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  
  try {
    const date = new Date(dateString);
    
    // Verificar si la fecha es válida
    if (isNaN(date.getTime())) return 'N/A';
    
    // Formatear: "14 Oct 2025, 00:36"
    const options: Intl.DateTimeFormatOptions = {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    
    return new Intl.DateTimeFormat('es-CL', options).format(date);
  } catch (error) {
    return 'N/A';
  }
};

// Lifecycle
onMounted(() => {
  fetchAnalyticsData();
});
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold text-gray-800 flex items-center gap-3">
          <i class="pi pi-chart-line text-blue-600"></i>
          Analítica Avanzada
        </h1>
        <p class="text-gray-600 mt-1">Análisis de correlaciones, anomalías y predicciones</p>
      </div>
      
      <div class="flex gap-2">
        <button
          @click="refreshData"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 shadow-md"
          :disabled="isLoading"
        >
          <i class="pi pi-refresh" :class="{ 'animate-spin': isLoading }"></i>
          Actualizar
        </button>
      </div>
    </div>

    <!-- Period Selector -->
    <div class="bg-white rounded-xl shadow-md p-4">
      <div class="flex flex-wrap items-center gap-4">
        <span class="text-gray-700 font-medium">Período de análisis:</span>
        <div class="flex gap-2">
          <button
            v-for="period in ['week', 'month', 'quarter']"
            :key="period"
            @click="selectedPeriod = period as any; fetchAnalyticsData();"
            class="px-4 py-2 rounded-lg transition-all"
            :class="selectedPeriod === period 
              ? 'bg-blue-600 text-white shadow-md' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
          >
            {{ period === 'week' ? 'Semana' : period === 'month' ? 'Mes' : 'Trimestre' }}
          </button>
        </div>
        
        <div class="ml-auto flex items-center gap-4">
            <div class="flex flex-col items-end gap-1">
            <button
              @click="exportToPDF"
              title="Genera un resumen en PDF con las métricas clave del período seleccionado"
              aria-label="Exportar resumen en PDF"
              class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
            >
              <i class="pi pi-file-pdf"></i>
              Resumen (PDF)
            </button>
          </div>

          <div class="flex flex-col items-end gap-1">
            <button
              @click="exportToExcel"
              title="Descarga un archivo Excel con todos los registros: fecha, medición y sensor"
              aria-label="Exportar datos completos en Excel"
              class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <i class="pi pi-file-excel"></i>
              Datos completos (Excel)
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center py-20">
      <div class="text-center">
        <i class="pi pi-spin pi-spinner text-4xl text-blue-600 mb-4"></i>
        <p class="text-gray-600">Cargando datos analíticos...</p>
      </div>
    </div>

    <template v-else>
      <!-- Correlation Analysis -->
      <div class="bg-white rounded-xl shadow-md p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
            <i class="pi pi-sitemap text-blue-600"></i>
            Correlación entre Variables
          </h2>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Variable Selection -->
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Variable 1</label>
              <select
                v-model="correlationVars.var1"
                @change="calculateCorrelation"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option v-for="opt in availableVars" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Variable 2</label>
              <select
                v-model="correlationVars.var2"
                @change="calculateCorrelation"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option v-for="opt in availableVars" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <button
              @click="calculateCorrelation"
              class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Calcular Correlación
            </button>
          </div>

          <!-- Correlation Result -->
          <div class="lg:col-span-2 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
            <div v-if="correlationData" class="space-y-4">
              <div class="text-center">
                <p class="text-gray-600 text-sm mb-2">Coeficiente de Correlación</p>
                <p class="text-5xl font-bold text-blue-600 mb-2">{{ correlationCoefficient }}</p>
                <p class="text-lg" :class="correlationStrength.color">
                  Correlación {{ correlationStrength.label }}
                </p>
              </div>

              <div class="grid grid-cols-2 gap-4 mt-6">
                <div class="bg-white rounded-lg p-4 text-center">
                  <p class="text-gray-600 text-sm">{{ getVariableLabel(correlationVars.var1) }}</p>
                  <p class="text-2xl font-bold text-gray-800">
                    {{ formatNumber(correlationData.var1_mean, 2) }}
                  </p>
                  <p class="text-xs text-gray-500">Promedio</p>
                </div>
                <div class="bg-white rounded-lg p-4 text-center">
                  <p class="text-gray-600 text-sm">{{ getVariableLabel(correlationVars.var2) }}</p>
                  <p class="text-2xl font-bold text-gray-800">
                    {{ formatNumber(correlationData.var2_mean, 2) }}
                  </p>
                  <p class="text-xs text-gray-500">Promedio</p>
                </div>
              </div>

              <div class="bg-blue-600 text-white rounded-lg p-4 mt-4">
                <p class="text-sm">
                  <i class="pi pi-info-circle mr-2"></i>
                  <span v-if="Math.abs(parseFloat(correlationCoefficient || '0')) >= 0.7">
                    Existe una correlación <strong>fuerte</strong> entre estas variables. Los cambios en una afectan significativamente a la otra.
                  </span>
                  <span v-else-if="Math.abs(parseFloat(correlationCoefficient || '0')) >= 0.4">
                    Existe una correlación <strong>moderada</strong> entre estas variables. Hay cierta relación pero no es determinante.
                  </span>
                  <span v-else>
                    La correlación es <strong>débil</strong>. Estas variables no muestran una relación significativa.
                  </span>
                </p>
              </div>
            </div>
            <div v-else class="text-center text-gray-500 py-8">
              <i class="pi pi-chart-line text-4xl mb-2"></i>
              <p>Selecciona las variables y calcula la correlación</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Historical Comparison -->
      <div class="bg-white rounded-xl shadow-md p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
            <i class="pi pi-calendar text-green-600"></i>
            Comparativa Histórica
          </h2>
        </div>

        <div v-if="currentPeriodStats" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Current Period -->
            <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6">
              <h3 class="text-lg font-semibold text-green-800 mb-4">{{ periodLabel }}</h3>
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">pH Promedio</span>
                  <span class="text-xl font-bold text-green-800">{{ formatNumber(currentPeriodStats.avgPH, 2) }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">Temp. Promedio</span>
                  <span class="text-xl font-bold text-green-800">{{ formatNumber(currentPeriodStats.avgTemp, 1) }}°C</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">EC Promedio</span>
                  <span class="text-xl font-bold text-green-800">{{ formatNumber(currentPeriodStats.avgEC, 0) }} µS/cm</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">Lecturas Totales</span>
                  <span class="text-xl font-bold text-green-800">{{ currentPeriodStats.totalReadings || 'N/A' }}</span>
                </div>
              </div>
            </div>

            <!-- Previous Period -->
            <div v-if="previousPeriodStats" class="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-6">
              <h3 class="text-lg font-semibold text-gray-800 mb-4">Período Anterior</h3>
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">pH Promedio</span>
                  <span class="text-xl font-bold text-gray-800">{{ formatNumber(previousPeriodStats.avgPH, 2) }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">Temp. Promedio</span>
                  <span class="text-xl font-bold text-gray-800">{{ formatNumber(previousPeriodStats.avgTemp, 1) }}°C</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">EC Promedio</span>
                  <span class="text-xl font-bold text-gray-800">{{ formatNumber(previousPeriodStats.avgEC, 0) }} µS/cm</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">Lecturas Totales</span>
                  <span class="text-xl font-bold text-gray-800">{{ previousPeriodStats.totalReadings || 'N/A' }}</span>
                </div>
              </div>
            </div>
            
            <!-- No Previous Data Message -->
            <div v-else class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6 flex items-center justify-center">
              <div class="text-center">
                <i class="pi pi-info-circle text-4xl text-blue-600 mb-3"></i>
                <h3 class="text-lg font-semibold text-blue-800 mb-2">Sin Datos Anteriores</h3>
                <p class="text-sm text-blue-700">
                  No hay datos suficientes del período anterior para realizar la comparación.
                </p>
              </div>
            </div>
          </div>

          <!-- Growth Indicator -->
          <div v-if="growthPercentage !== null" class="bg-blue-50 border-l-4 border-blue-600 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <i 
                  class="pi text-2xl"
                  :class="{
                    'pi-arrow-up text-green-600': parseFloatSafe(growthPercentage) > 0,
                    'pi-arrow-down text-red-600': parseFloatSafe(growthPercentage) < 0,
                    'pi-minus text-gray-600': parseFloatSafe(growthPercentage) === 0
                  }"
                ></i>
                <div>
                  <p class="text-sm text-gray-600">Variación de pH</p>
                  <p class="text-2xl font-bold" :class="{
                    'text-green-600': parseFloatSafe(growthPercentage) > 0,
                    'text-red-600': parseFloatSafe(growthPercentage) < 0,
                    'text-gray-600': parseFloatSafe(growthPercentage) === 0
                  }">
                    {{ growthPercentage }}%
                  </p>
                </div>
              </div>
              <p class="text-sm text-gray-700 max-w-md">
                <span v-if="parseFloatSafe(growthPercentage) > 0">
                  El pH ha aumentado en promedio respecto al período anterior.
                </span>
                <span v-else-if="parseFloatSafe(growthPercentage) < 0">
                  El pH ha disminuido en promedio respecto al período anterior.
                </span>
                <span v-else>
                  El pH se mantiene estable respecto al período anterior.
                </span>
              </p>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-500 py-8">
          <i class="pi pi-calendar text-4xl mb-2"></i>
          <p>Cargando datos de comparativa...</p>
        </div>
      </div>

      <!-- Anomaly Detection (moved to end with pagination) -->
      <div class="bg-white rounded-xl shadow-md p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
            <i class="pi pi-exclamation-triangle text-orange-600"></i>
            Detección de Anomalías
          </h2>
          <span class="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
            {{ anomalies.length }} anomalías detectadas
          </span>
        </div>

        <div v-if="anomalies.length > 0" class="space-y-3">
          <div
            v-for="(anomaly, index) in paginatedAnomalies"
            :key="index"
            class="bg-orange-50 border-l-4 border-orange-500 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <i class="pi pi-bolt text-orange-600"></i>
                  <span class="font-medium text-gray-800">{{ getVariableLabel(anomaly.sensor_type) || 'Sensor' }}</span>
                  <span class="text-xs text-gray-500">{{ formatDateTime(anomaly.timestamp) }}</span>
                </div>
                <p class="text-sm text-gray-700">
                  Valor detectado: <strong>{{ formatNumber(anomaly.value, 2) }}</strong>
                  (esperado: {{ anomaly.expected_range || 'N/A' }})
                </p>
                <p class="text-xs text-gray-600 mt-1">
                  {{ anomaly.description || 'Patrón inusual detectado por el modelo de ML' }}
                </p>
              </div>
              <div class="text-right">
                <span class="px-2 py-1 bg-orange-600 text-white rounded text-xs font-bold">
                  {{ anomaly.severity || 'Media' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Pagination Controls -->
          <div v-if="totalAnomaliesPages > 1" class="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
            <div class="text-sm text-gray-600">
              Mostrando {{ (anomaliesPage - 1) * anomaliesPerPage + 1 }} - {{ Math.min(anomaliesPage * anomaliesPerPage, anomalies.length) }} de {{ anomalies.length }} anomalías
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="anomaliesPage--"
                :disabled="anomaliesPage === 1"
                class="px-4 py-2 rounded-lg transition-colors flex items-center gap-1"
                :class="anomaliesPage === 1 
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                  : 'bg-orange-100 text-orange-700 hover:bg-orange-200'"
              >
                <i class="pi pi-chevron-left text-sm"></i>
                Anterior
              </button>
              
              <div class="flex items-center gap-1">
                <template v-for="page in totalAnomaliesPages" :key="page">
                  <button
                    v-if="page === 1 || page === totalAnomaliesPages || (page >= anomaliesPage - 1 && page <= anomaliesPage + 1)"
                    @click="anomaliesPage = page"
                    class="w-10 h-10 rounded-lg transition-colors font-medium"
                    :class="anomaliesPage === page 
                      ? 'bg-orange-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                  >
                    {{ page }}
                  </button>
                  <span 
                    v-else-if="page === 2 && anomaliesPage > 3"
                    class="text-gray-400 px-1"
                  >...</span>
                  <span 
                    v-else-if="page === totalAnomaliesPages - 1 && anomaliesPage < totalAnomaliesPages - 2"
                    class="text-gray-400 px-1"
                  >...</span>
                </template>
              </div>

              <button
                @click="anomaliesPage++"
                :disabled="anomaliesPage === totalAnomaliesPages"
                class="px-4 py-2 rounded-lg transition-colors flex items-center gap-1"
                :class="anomaliesPage === totalAnomaliesPages 
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                  : 'bg-orange-100 text-orange-700 hover:bg-orange-200'"
              >
                Siguiente
                <i class="pi pi-chevron-right text-sm"></i>
              </button>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-500 py-8">
          <i class="pi pi-check-circle text-4xl text-green-600 mb-2"></i>
          <p>No se detectaron anomalías en el período seleccionado</p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* Animaciones adicionales si es necesario */
</style>
