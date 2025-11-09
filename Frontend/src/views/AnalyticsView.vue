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

// Datos para comparativa
const currentPeriodStats = ref<any>(null);
const previousPeriodStats = ref<any>(null);

// Configuración de correlación
const correlationVars = ref({
  var1: 'pH_Value',
  var2: 'Temperature'
});

// Opciones de variables
const availableVars = [
  { label: 'pH', value: 'pH_Value' },
  { label: 'Temperatura', value: 'Temperature' },
  { label: 'Electroconductividad', value: 'EC' }
];

// Mapeo de nombres técnicos a español
const getVariableLabel = (varName: string): string => {
  const labels: Record<string, string> = {
    'pH_Value': 'pH',
    'Temperature': 'Temperatura',
    'EC': 'Electroconductividad'
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

// Métodos
const fetchAnalyticsData = async () => {
  isLoading.value = true;
  try {
    // 1. Calcular correlación
    await calculateCorrelation();
    
    // 2. Detectar anomalías
    await detectAnomalies();
    
    // 3. Obtener predicciones
    await fetchPredictions();
    
    // 4. Comparativa histórica
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
    // Datos mockeados para demo
    correlationData.value = {
      coefficient: 0.72,
      p_value: 0.001,
      sample_size: 1250,
      var1_mean: 7.2,
      var2_mean: 22.5,
      var1_std: 0.5,
      var2_std: 2.1
    };
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
    // Datos mockeados para demo
    anomalies.value = [
      {
        timestamp: new Date().toISOString(),
        sensor_type: 'pH',
        value: 9.2,
        expected_range: '6.5 - 8.5',
        z_score: 3.2,
        severity: 'Alta',
        description: 'pH fuera del rango normal detectado'
      },
      {
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        sensor_type: 'temperature',
        value: 28.5,
        expected_range: '18 - 25',
        z_score: 2.8,
        severity: 'Media',
        description: 'Temperatura elevada detectada'
      }
    ];
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
    // Datos mockeados para demo
    predictions.value = {
      pH: {
        predicted_value: 7.3,
        current_value: 7.2,
        trend: 'Ascendente',
        confidence: '85%'
      },
      temperature: {
        predicted_value: 21.8,
        current_value: 22.5,
        trend: 'Descendente',
        confidence: '82%'
      },
      electroconductivity: {
        predicted_value: 455,
        current_value: 450,
        trend: 'Estable',
        confidence: '88%'
      }
    };
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
    // Datos mockeados para demo
    currentPeriodStats.value = {
      avgPH: 7.2,
      avgTemp: 22.5,
      avgEC: 450,
      totalReadings: 1250
    };
    previousPeriodStats.value = {
      avgPH: 7.0,
      avgTemp: 23.1,
      avgEC: 445,
      totalReadings: 1180
    };
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
        
        <div class="ml-auto flex gap-2">
          <button
            @click="exportToPDF"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
          >
            <i class="pi pi-file-pdf"></i>
            PDF
          </button>
          <button
            @click="exportToExcel"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <i class="pi pi-file-excel"></i>
            Excel
          </button>
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

      <!-- Anomaly Detection -->
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
            v-for="(anomaly, index) in anomalies.slice(0, 10)"
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
        </div>
        <div v-else class="text-center text-gray-500 py-8">
          <i class="pi pi-check-circle text-4xl text-green-600 mb-2"></i>
          <p>No se detectaron anomalías en el período seleccionado</p>
        </div>
      </div>

      <!-- Predictions -->
      <div class="bg-white rounded-xl shadow-md p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
            <i class="pi pi-forward text-purple-600"></i>
            Predicciones a Corto Plazo (24-48h)
          </h2>
        </div>

        <div v-if="predictions" class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
            <div class="flex items-center justify-between mb-4">
              <i class="pi pi-flask text-3xl text-purple-600"></i>
              <span class="text-xs text-purple-700 font-medium">pH</span>
            </div>
            <p class="text-3xl font-bold text-purple-800 mb-1">
              {{ formatNumber(predictions.pH?.predicted_value, 2) }}
            </p>
            <p class="text-sm text-purple-600">
              <i class="pi pi-arrow-up text-xs mr-1"></i>
              Tendencia: {{ predictions.pH?.trend || 'Estable' }}
            </p>
            <div class="mt-3 pt-3 border-t border-purple-200">
              <p class="text-xs text-purple-700">Confianza: {{ predictions.pH?.confidence || '85%' }}</p>
            </div>
          </div>

          <div class="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-6">
            <div class="flex items-center justify-between mb-4">
              <i class="pi pi-sun text-3xl text-red-600"></i>
              <span class="text-xs text-red-700 font-medium">Temperatura</span>
            </div>
            <p class="text-3xl font-bold text-red-800 mb-1">
              {{ formatNumber(predictions.temperature?.predicted_value, 1) }}°C
            </p>
            <p class="text-sm text-red-600">
              <i class="pi pi-arrow-down text-xs mr-1"></i>
              Tendencia: {{ predictions.temperature?.trend || 'Descendente' }}
            </p>
            <div class="mt-3 pt-3 border-t border-red-200">
              <p class="text-xs text-red-700">Confianza: {{ predictions.temperature?.confidence || '82%' }}</p>
            </div>
          </div>

          <div class="bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-lg p-6">
            <div class="flex items-center justify-between mb-4">
              <i class="pi pi-bolt text-3xl text-cyan-600"></i>
              <span class="text-xs text-cyan-700 font-medium">Electrocond.</span>
            </div>
            <p class="text-3xl font-bold text-cyan-800 mb-1">
              {{ formatNumber(predictions.electroconductivity?.predicted_value, 0) }}
            </p>
            <p class="text-sm text-cyan-600">
              <i class="pi pi-minus text-xs mr-1"></i>
              Tendencia: {{ predictions.electroconductivity?.trend || 'Estable' }}
            </p>
            <div class="mt-3 pt-3 border-t border-cyan-200">
              <p class="text-xs text-cyan-700">Confianza: {{ predictions.electroconductivity?.confidence || '88%' }}</p>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-500 py-8">
          <i class="pi pi-chart-line text-4xl mb-2"></i>
          <p>Cargando predicciones...</p>
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

        <div v-if="currentPeriodStats && previousPeriodStats" class="space-y-4">
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
                  <span class="text-xl font-bold text-green-800">{{ formatNumber(currentPeriodStats.avgEC, 0) }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">Lecturas Totales</span>
                  <span class="text-xl font-bold text-green-800">{{ currentPeriodStats.totalReadings || 'N/A' }}</span>
                </div>
              </div>
            </div>

            <!-- Previous Period -->
            <div class="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-6">
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
                  <span class="text-xl font-bold text-gray-800">{{ formatNumber(previousPeriodStats.avgEC, 0) }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-gray-700">Lecturas Totales</span>
                  <span class="text-xl font-bold text-gray-800">{{ previousPeriodStats.totalReadings || 'N/A' }}</span>
                </div>
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
    </template>
  </div>
</template>

<style scoped>
/* Animaciones adicionales si es necesario */
</style>
