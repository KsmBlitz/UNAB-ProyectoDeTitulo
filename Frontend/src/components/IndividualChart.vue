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
const showPrediction = ref(false);
const isPredictionLoading = ref(false);
const predictionData = ref<any>(null);

// Modal de configuración del modelo
const showConfigModal = ref(false);
const modelConfig = ref({
  days: 5,
  lookback_days: 7
});
const isSavingConfig = ref(false);

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
  isLoading.value = true;
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
      labels: data.labels || [],
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
  currentTimeRange.value = hours;
  fetchData();
};

const refreshData = async () => {
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
    
    // Close modal
    showConfigModal.value = false;
    
    // Reload prediction if it's currently showing
    if (showPrediction.value) {
      await loadPrediction();
    }
    
  } catch (err) {
    console.error('Error saving model config:', err);
    alert('Error al guardar la configuración del modelo');
  } finally {
    isSavingConfig.value = false;
  }
};

// Toggle prediction visibility
const togglePrediction = async () => {
  showPrediction.value = !showPrediction.value;
  
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
        
        <!-- Prediction toggle button (only for pH and conductivity) -->
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
        
        <!-- Config button for prediction model -->
        <button
          v-if="sensorType === 'ph' || sensorType === 'conductividad'"
          @click="openConfigModal"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-1.5 bg-gray-100 text-gray-700 hover:bg-gray-200"
          title="Configurar modelo de predicción"
        >
          <i class="pi pi-cog"></i>
        </button>
        
        <span v-if="isLoading" class="text-primary-500">
          <i class="pi pi-spin pi-spinner"></i>
        </span>
        <span v-else-if="error" class="text-danger-500">
          <i class="pi pi-exclamation-triangle"></i>
        </span>
        <span v-else class="text-success-500">
          <i class="pi pi-check-circle"></i>
        </span>
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
  <div
    v-if="showConfigModal"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="showConfigModal = false"
  >
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-bold text-gray-800 dark:text-white">
          Configuración del Modelo de Predicción
        </h3>
        <button
          @click="showConfigModal = false"
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <i class="pi pi-times"></i>
        </button>
      </div>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Días a predecir
          </label>
          <input
            v-model.number="modelConfig.days"
            type="number"
            min="1"
            max="30"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Cantidad de días hacia adelante que predecirá el modelo (1-30)
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Días históricos para entrenar
          </label>
          <input
            v-model.number="modelConfig.lookback_days"
            type="number"
            min="1"
            max="90"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Cantidad de días históricos para entrenar el modelo (1-90)
          </p>
        </div>
        
        <div class="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
          <div class="flex items-start gap-2">
            <i class="pi pi-info-circle text-blue-500 mt-0.5"></i>
            <div class="text-xs text-blue-700 dark:text-blue-200">
              <p class="font-semibold mb-1">Recomendaciones:</p>
              <ul class="list-disc list-inside space-y-1">
                <li>Más días históricos = Mayor precisión (si hay datos suficientes)</li>
                <li>Predicciones a largo plazo (>7 días) son menos precisas</li>
                <li>Los cambios se registrarán en el historial de auditoría</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
      <div class="flex gap-3 mt-6">
        <button
          @click="showConfigModal = false"
          class="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Cancelar
        </button>
        <button
          @click="saveModelConfig"
          :disabled="isSavingConfig"
          class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <i v-if="isSavingConfig" class="pi pi-spin pi-spinner"></i>
          <span>{{ isSavingConfig ? 'Guardando...' : 'Guardar' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
