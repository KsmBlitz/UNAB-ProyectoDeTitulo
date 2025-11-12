<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<!-- Frontend/src/components/IndividualChart.vue -->
<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { Line } from 'vue-chartjs';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartData
} from 'chart.js';
import { API_BASE_URL } from '@/config/api';
import { authStore } from '@/auth/store';
import { notify } from '@/stores/notificationStore';
import { evaluateMetricStatus, BLUEBERRY_THRESHOLDS, type MetricStatus } from '@/utils/metrics';

defineOptions({
  name: 'IndividualChart'
});

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const props = defineProps<{
  sensorType: string;  // 'temperatura', 'ph', 'conductividad', 'nivel'
  title: string;
  timeRange: number;
  color: string;
  icon: string;
  unit: string;
}>();

const chartData = ref<ChartData<'line'>>({ labels: [], datasets: [] });
const isLoading = ref(true);
const error = ref<string | null>(null);
const currentTimeRange = ref(props.timeRange);

// Cargar estado de predicción desde localStorage
const savedPredictionState = localStorage.getItem(`prediction_${props.sensorType}_enabled`);
const showPrediction = ref(savedPredictionState === 'true');
const isPredictionLoading = ref(false);
const predictionData = ref<any>(null);

// Modal de configuración del modelo
const showConfigModal = ref(false);

// Cargar configuración del modelo desde localStorage o usar defaults
const getStoredConfig = () => {
  const stored = localStorage.getItem(`prediction_${props.sensorType}_config`);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return { days: 5, lookback_days: 7 };
    }
  }
  return { days: 5, lookback_days: 7 };
};

const modelConfig = ref(getStoredConfig());
const isSavingConfig = ref(false);

// Authorization - Verificar que el usuario sea administrador
const isAdmin = computed(() => {
  const userRole = authStore.user?.role;
  return userRole === 'admin';
});

// Computed property to check for critical predictions
const criticalPredictions = computed(() => {
  if (!predictionData.value || !showPrediction.value) return { hasCritical: false, hasWarning: false, count: 0 };
  
  // Get thresholds for current sensor type
  let thresholds;
  if (props.sensorType === 'ph') {
    thresholds = BLUEBERRY_THRESHOLDS.ph;
  } else if (props.sensorType === 'conductividad') {
    thresholds = BLUEBERRY_THRESHOLDS.conductivity;
  } else {
    return { hasCritical: false, hasWarning: false, count: 0 };
  }
  
  let criticalCount = 0;
  let warningCount = 0;
  
  predictionData.value.predictions.forEach((pred: any) => {
    const status = evaluateMetricStatus(pred.value, thresholds);
    if (status === 'critical') criticalCount++;
    if (status === 'warning') warningCount++;
  });
  
  return {
    hasCritical: criticalCount > 0,
    hasWarning: warningCount > 0,
    count: criticalCount + warningCount
  };
});

// Opciones de gráfico optimizadas para gráfico individual
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false, // IMPORTANTE: Para que respete el contenedor
  interaction: {
    intersect: false,
    mode: 'index' as const,
  },
  plugins: {
    legend: {
      display: false, // Hide legend to avoid duplicate labels
      position: 'top' as const,
      labels: {
        font: {
          size: 11
        },
        usePointStyle: true
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      callbacks: {
        label: (context: any) => {
          const label = context.dataset.label || '';
          return `${label}: ${context.parsed.y} ${props.unit}`;
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      ticks: {
        maxTicksLimit: 6, // Limitar etiquetas en el eje X
        font: {
          size: 11 // Texto más pequeño
        }
      }
    },
    y: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      beginAtZero: false,
      ticks: {
        maxTicksLimit: 5, // Limitar etiquetas en el eje Y
        font: {
          size: 11 // Texto más pequeño
        },
        callback: (value: any) => {
          return `${value} ${props.unit}`;
        }
      }
    }
  }
};

const fetchData = async () => {
  // Solo mostrar loading en la primera carga
  if (!chartData.value || chartData.value.labels?.length === 0) {
    isLoading.value = true;
  }
  
  error.value = null;

  const token = localStorage.getItem('userToken');

  try {
  
    const response = await fetch(
      `${API_BASE_URL}/api/charts/historical-data?sensor_type=${props.sensorType}&hours=${currentTimeRange.value}`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );

    if (!response.ok) {
      throw new Error('Error al cargar datos históricos');
    }

    const data = await response.json();

    // Las fechas ya vienen en hora de Chile desde el backend (sin timezone info)
    // Solo necesitamos extraer la hora (HH:MM)
    const localLabels = (data.labels || []).map((isoString: string) => {
      if (!isoString) return '';
      try {
        const date = new Date(isoString);
        // Verificar si la fecha es válida
        if (isNaN(date.getTime())) {
          return '';
        }
        // Extraer hora y minutos directamente (ya están en hora de Chile)
        return date.toLocaleTimeString('es-CL', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false
        });
      } catch (e) {
        return '';
      }
    });

    // Crear dataset según el tipo de sensor
    let datasetData = [];
    let datasetLabel = '';

    switch (props.sensorType) {
      case 'temperatura':
        datasetData = data.temperatura || [];
        datasetLabel = `Temperatura (${props.unit})`;
        break;
      case 'ph':
        datasetData = data.ph || [];
        datasetLabel = 'Nivel de pH';
        break;
      case 'conductividad':
        datasetData = data.conductividad || [];
        datasetLabel = `Conductividad (${props.unit})`;
        break;
      case 'nivel':
        datasetData = data.nivel_agua || [];
        datasetLabel = `Nivel del Agua (${props.unit})`;
        break;
    }

    chartData.value = {
      labels: localLabels,
      datasets: [
        {
          label: datasetLabel,
          data: datasetData,
          borderColor: props.color,
          backgroundColor: `${props.color}20`, // Color con 20% de opacidad
          tension: 0.4,
          fill: true,
          pointRadius: 1, // Puntos más pequeños
          pointHoverRadius: 4,
          borderWidth: 2
        }
      ]
    };

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Error desconocido';

    // Datos de ejemplo si falla
    chartData.value = {
      labels: ['10:00', '11:00', '12:00', '13:00', '14:00'],
      datasets: [
        {
          label: props.title,
          data: [20, 21, 22, 21, 20], // Datos de ejemplo
          borderColor: props.color,
          backgroundColor: `${props.color}20`,
          tension: 0.4,
          fill: true,
          pointRadius: 1,
          borderWidth: 2
        }
      ]
    };
  } finally {
    isLoading.value = false;
  }
};

// Funciones expuestas para control externo
const updateTimeRange = (hours: number) => {
  // Evitar actualizar si ya está cargando (throttling)
  if (isLoading.value) {
    return;
  }
  
  currentTimeRange.value = hours;
  fetchData();
};

const refreshData = async () => {
  // Evitar refresh si ya está cargando
  if (isLoading.value) {
    return;
  }
  
  await fetchData();
};

// Open config modal
const openConfigModal = () => {
  showConfigModal.value = true;
};

// Save model configuration
const saveModelConfig = async () => {
  isSavingConfig.value = true;
  
  try {
    const token = localStorage.getItem('userToken');
    
    // Save configuration to backend for audit logging
    const response = await fetch(`${API_BASE_URL}/api/sensors/prediction-config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        sensor_type: props.sensorType,
        days: modelConfig.value.days,
        lookback_days: modelConfig.value.lookback_days
      })
    });
    
    if (!response.ok) {
      throw new Error('Error al guardar configuración');
    }
    
    // Save configuration to localStorage
    localStorage.setItem(`prediction_${props.sensorType}_config`, JSON.stringify(modelConfig.value));
    
    // Show success notification
    notify.success(
      'Configuración guardada',
      `Predicción: ${modelConfig.value.days} días con ${modelConfig.value.lookback_days} días de histórico`
    );
    
    // Close modal
    showConfigModal.value = false;
    
    // Reload prediction if it's currently showing
    if (showPrediction.value) {
      await loadPrediction();
    }
    
  } catch (err) {
    console.error('Error saving model config:', err);
    notify.error(
      'Error al guardar',
      'No se pudo guardar la configuración del modelo. Intenta nuevamente.'
    );
  } finally {
    isSavingConfig.value = false;
  }
};

// Toggle prediction visibility
const togglePrediction = async () => {
  showPrediction.value = !showPrediction.value;
  
  // Save prediction state to localStorage
  localStorage.setItem(`prediction_${props.sensorType}_enabled`, showPrediction.value.toString());
  
  if (showPrediction.value) {
    await loadPrediction();
  } else {
    // Remove prediction dataset when hiding
    updateChartWithPrediction(null);
  }
};

// Load prediction data from API
const loadPrediction = async () => {
  isPredictionLoading.value = true;
  
  try {
    const token = localStorage.getItem('userToken');
    
    // Map sensor type to API parameter
    const sensorTypeMap: Record<string, string> = {
      'ph': 'ph',
      'conductividad': 'conductivity'
    };
    
    const apiSensorType = sensorTypeMap[props.sensorType];
    if (!apiSensorType) {
      console.error('Invalid sensor type for prediction:', props.sensorType);
      return;
    }
    
    const response = await fetch(
      `${API_BASE_URL}/api/sensors/predict/${apiSensorType}?days=${modelConfig.value.days}&lookback_days=${modelConfig.value.lookback_days}`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    if (!response.ok) {
      throw new Error('Error al cargar predicción');
    }
    
    const data = await response.json();
    
    if (data.success && data.predictions && data.predictions.length > 0) {
      predictionData.value = data;
      updateChartWithPrediction(data);
    } else {
      console.warn('No prediction data available:', data.message);
      predictionData.value = null;
      showPrediction.value = false;
    }
  } catch (error) {
    console.error('Error loading prediction:', error);
    predictionData.value = null;
    showPrediction.value = false;
  } finally {
    isPredictionLoading.value = false;
  }
};

// Update chart to include prediction line
const updateChartWithPrediction = (prediction: any) => {
  if (!chartData.value.datasets || chartData.value.datasets.length === 0) {
    return;
  }
  
  // Keep only the historical data dataset (first one)
  const historicalDataset = chartData.value.datasets[0];
  
  if (!prediction) {
    // Remove prediction - keep only historical
    chartData.value = {
      ...chartData.value,
      datasets: [historicalDataset]
    };
    return;
  }
  
  // Get current labels and data
  const currentLabels = [...(chartData.value.labels || [])];
  const currentData = [...historicalDataset.data];
  
  // Add prediction points
  const predictionLabels: string[] = [];
  const predictionValues: number[] = [];
  
  // Start prediction from last historical point
  const lastValue = currentData[currentData.length - 1];
  predictionValues.push(lastValue as number);
  predictionLabels.push(currentLabels[currentLabels.length - 1] as string);
  
  // Add predicted values
  prediction.predictions.forEach((pred: any) => {
    const date = new Date(pred.timestamp);
    const label = `${date.getDate()}/${date.getMonth() + 1}`;
    predictionLabels.push(label);
    predictionValues.push(pred.value);
  });
  
  // Determine prediction line color based on critical status
  let predictionColor = props.color;
  let predictionBgColor = 'transparent';
  
  // Get thresholds for current sensor type
  if (props.sensorType === 'ph' || props.sensorType === 'conductividad') {
    const thresholds = props.sensorType === 'ph' 
      ? BLUEBERRY_THRESHOLDS.ph 
      : BLUEBERRY_THRESHOLDS.conductivity;
    
    // Check if any prediction is critical or warning
    let hasCritical = false;
    let hasWarning = false;
    
    prediction.predictions.forEach((pred: any) => {
      const status = evaluateMetricStatus(pred.value, thresholds);
      if (status === 'critical') hasCritical = true;
      if (status === 'warning') hasWarning = true;
    });
    
    // Change color based on worst status
    if (hasCritical) {
      predictionColor = '#dc3545'; // Red for critical
      predictionBgColor = 'rgba(220, 53, 69, 0.1)';
    } else if (hasWarning) {
      predictionColor = '#ffc107'; // Yellow for warning
      predictionBgColor = 'rgba(255, 193, 7, 0.1)';
    }
  }
  
  // Create prediction dataset
  const predictionDataset = {
    label: 'Predicción',
    data: Array(currentData.length - 1).fill(null).concat(predictionValues),
    borderColor: predictionColor,
    backgroundColor: predictionBgColor,
    borderDash: [5, 5], // Dashed line
    tension: 0.4,
    fill: false,
    pointRadius: 3,
    pointHoverRadius: 5,
    borderWidth: 2,
    pointStyle: 'circle',
    pointBackgroundColor: predictionColor
  };
  
  // Update chart with both datasets
  chartData.value = {
    labels: [...currentLabels, ...predictionLabels.slice(1)],
    datasets: [historicalDataset, predictionDataset]
  };
};

// Exponer funciones al componente padre
defineExpose({
  updateTimeRange,
  refreshData
});

// Watch para cambios en timeRange (prop)
watch(() => props.timeRange, (newRange) => {
  currentTimeRange.value = newRange;
  fetchData();
});

onMounted(fetchData);
</script>

<template>
  <div class="h-full bg-white rounded-lg p-4 flex flex-col overflow-hidden">
    <!-- Header del gráfico individual -->
    <div class="flex justify-between items-center mb-4 pb-2 border-b border-gray-200 flex-shrink-0">
      <div class="flex items-center gap-2">
        <i :class="icon" class="text-base" :style="{ color: props.color }"></i>
        <h4 class="m-0 text-sm font-semibold text-gray-800">{{ title }}</h4>
      </div>
      <div class="flex items-center gap-2">
        <!-- Warning badge for critical predictions -->
        <div
          v-if="showPrediction && criticalPredictions.hasCritical"
          class="px-2 py-1 rounded-md bg-red-100 text-red-700 text-xs font-semibold flex items-center gap-1"
          title="Predicción con valores críticos detectados"
        >
          <i class="pi pi-exclamation-triangle"></i>
          <span>Crítico</span>
        </div>
        <div
          v-else-if="showPrediction && criticalPredictions.hasWarning"
          class="px-2 py-1 rounded-md bg-yellow-100 text-yellow-700 text-xs font-semibold flex items-center gap-1"
          title="Predicción con valores de advertencia detectados"
        >
          <i class="pi pi-exclamation-circle"></i>
          <span>Advertencia</span>
        </div>
        
        <!-- Prediction toggle button (for pH and conductivity - all users) -->
        <button
          v-if="sensorType === 'ph' || sensorType === 'conductividad'"
          @click="togglePrediction"
          :disabled="isPredictionLoading"
          :class="showPrediction ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          :title="showPrediction ? 'Ocultar predicción' : 'Ver predicción'"
        >
          <i v-if="isPredictionLoading" class="pi pi-spin pi-spinner"></i>
          <i v-else :class="showPrediction ? 'pi pi-eye-slash' : 'pi pi-chart-line'"></i>
          <span>{{ showPrediction ? 'Ocultar' : 'Predicción' }}</span>
        </button>
        
        <!-- Config button for prediction model (only admin) -->
        <button
          v-if="(sensorType === 'ph' || sensorType === 'conductividad') && isAdmin"
          @click="openConfigModal"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 bg-gray-100 text-gray-700 hover:bg-gray-200"
          title="Configurar modelo de predicción"
        >
          <i class="pi pi-cog"></i>
        </button>
      </div>
    </div>

    <!-- Contenido del gráfico con ALTURA CONTROLADA -->
    <div class="flex-grow flex items-center justify-center min-h-0 overflow-hidden">
      <div v-if="error" class="flex flex-col items-center gap-2 text-danger-500 text-center">
        <i class="pi pi-exclamation-triangle"></i>
        <p class="m-0 text-xs">{{ error }}</p>
        <button
          @click="fetchData"
          class="px-3 py-1.5 bg-danger-500 text-white border-none rounded cursor-pointer text-xs hover:bg-danger-600 transition-colors"
        >
          Reintentar
        </button>
      </div>

      <div v-else-if="isLoading" class="flex flex-col items-center gap-2 text-gray-500 text-center">
        <i class="pi pi-spin pi-spinner"></i>
        <p class="m-0 text-xs">Cargando...</p>
      </div>

      <div v-else class="relative h-full w-full min-h-[200px] max-h-[280px] md:min-h-[180px] md:max-h-[250px]">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
  
  <!-- Modal de configuración del modelo -->
  <Teleport to="body">
    <div
      v-if="showConfigModal"
      class="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-[9999] p-4"
      @click.self="showConfigModal = false"
    >
      <div 
        class="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-fadeIn border border-gray-200"
        style="animation: slideUp 0.3s ease-out"
      >
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-5 border-b border-blue-100">
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-3">
              <div class="bg-blue-100 rounded-xl p-2.5">
                <i class="pi pi-sliders-h text-blue-600 text-xl"></i>
              </div>
              <div>
                <h3 class="text-xl font-bold text-gray-800">
                  Configuración del Modelo
                </h3>
                <p class="text-gray-600 text-sm">
                  Ajusta los parámetros de predicción
                </p>
              </div>
            </div>
            <button
              @click="showConfigModal = false"
              class="text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg p-2 transition-all"
            >
              <i class="pi pi-times text-xl"></i>
            </button>
          </div>
        </div>
        
        <!-- Body -->
        <div class="p-6 space-y-6 bg-white">
          <!-- Días a predecir -->
          <div class="space-y-2">
            <label class="flex items-center gap-2 text-sm font-semibold text-gray-700">
              <i class="pi pi-calendar text-blue-600"></i>
              Días a predecir
            </label>
            <div class="relative">
              <input
                v-model.number="modelConfig.days"
                type="number"
                min="1"
                max="30"
                class="w-full px-4 py-3 pr-12 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-800 transition-all text-lg font-semibold"
                placeholder="5"
              />
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-medium">
                días
              </span>
            </div>
            <div class="flex items-start gap-2 bg-blue-50 rounded-lg p-3 border border-blue-100">
              <i class="pi pi-info-circle text-blue-600 text-sm mt-0.5"></i>
              <p class="text-xs text-blue-800">
                Cantidad de días hacia adelante que predecirá el modelo (1-30)
              </p>
            </div>
          </div>
          
          <!-- Días históricos -->
          <div class="space-y-2">
            <label class="flex items-center gap-2 text-sm font-semibold text-gray-700">
              <i class="pi pi-history text-indigo-600"></i>
              Días históricos para entrenar
            </label>
            <div class="relative">
              <input
                v-model.number="modelConfig.lookback_days"
                type="number"
                min="1"
                max="90"
                class="w-full px-4 py-3 pr-12 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-800 transition-all text-lg font-semibold"
                placeholder="7"
              />
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-medium">
                días
              </span>
            </div>
            <div class="flex items-start gap-2 bg-indigo-50 rounded-lg p-3 border border-indigo-100">
              <i class="pi pi-info-circle text-indigo-600 text-sm mt-0.5"></i>
              <p class="text-xs text-indigo-800">
                Cantidad de días históricos para entrenar el modelo (1-90)
              </p>
            </div>
          </div>
          
          <!-- Recomendaciones -->
          <div class="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-4">
            <div class="flex items-start gap-3">
              <div class="bg-amber-100 rounded-lg p-2 mt-0.5">
                <i class="pi pi-lightbulb text-amber-600"></i>
              </div>
              <div class="flex-1">
                <p class="font-semibold text-amber-900 text-sm mb-2">
                  Recomendaciones
                </p>
                <ul class="space-y-1.5 text-xs text-amber-800">
                  <li class="flex items-start gap-2">
                    <i class="pi pi-check-circle text-amber-600 mt-0.5 text-xs"></i>
                    <span>Más días históricos = Mayor precisión (si hay datos suficientes)</span>
                  </li>
                  <li class="flex items-start gap-2">
                    <i class="pi pi-check-circle text-amber-600 mt-0.5 text-xs"></i>
                    <span>Predicciones a largo plazo (>7 días) son menos precisas</span>
                  </li>
                  <li class="flex items-start gap-2">
                    <i class="pi pi-check-circle text-amber-600 mt-0.5 text-xs"></i>
                    <span>Los cambios se registrarán en el historial de auditoría</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="bg-gray-50 border-t border-gray-200 px-6 py-4 flex gap-3">
          <button
            @click="showConfigModal = false"
            class="flex-1 px-4 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-100 transition-all font-semibold"
          >
            Cancelar
          </button>
          <button
            @click="saveModelConfig"
            :disabled="isSavingConfig"
            class="flex-1 px-4 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold shadow-lg"
          >
            <i v-if="isSavingConfig" class="pi pi-spin pi-spinner"></i>
            <i v-else class="pi pi-check"></i>
            <span>{{ isSavingConfig ? 'Guardando...' : 'Guardar Cambios' }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
