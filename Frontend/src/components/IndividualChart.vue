<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<!-- Frontend/src/components/IndividualChart.vue -->
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
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
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

defineOptions({
  name: 'IndividualChart'
});

// ✅ REGISTRAR EL PLUGIN FILLER
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
      display: false, // Sin leyenda para gráficos individuales
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      callbacks: {
        label: (context: any) => {
          return `${context.parsed.y} ${props.unit}`;
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
    // ✅ CAMBIAR URL
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
      <div class="flex items-center">
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
</template>
