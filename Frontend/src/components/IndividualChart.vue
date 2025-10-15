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
  <div class="individual-chart">
    <!-- Header del gráfico individual -->
    <div class="chart-header">
      <div class="chart-title">
        <i :class="icon" class="chart-icon"></i>
        <h4>{{ title }}</h4>
      </div>
      <div class="chart-status">
        <span v-if="isLoading" class="status-loading">
          <i class="pi pi-spin pi-spinner"></i>
        </span>
        <span v-else-if="error" class="status-error">
          <i class="pi pi-exclamation-triangle"></i>
        </span>
        <span v-else class="status-success">
          <i class="pi pi-check-circle"></i>
        </span>
      </div>
    </div>

    <!-- Contenido del gráfico con ALTURA CONTROLADA -->
    <div class="chart-content">
      <div v-if="error" class="error-state">
        <i class="pi pi-exclamation-triangle"></i>
        <p>{{ error }}</p>
        <button @click="fetchData" class="retry-btn">Reintentar</button>
      </div>

      <div v-else-if="isLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i>
        <p>Cargando...</p>
      </div>

      <div v-else class="chart-wrapper">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.individual-chart {
  height: 100%; /* IMPORTANTE: Ocupa todo el espacio del contenedor padre */
  background-color: #fff;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* IMPORTANTE: Evita el crecimiento infinito */
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0; /* No se encoge */
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-icon {
  font-size: 1rem;
  color: v-bind('props.color');
}

.chart-title h4 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
}

.chart-status {
  display: flex;
  align-items: center;
}

.status-loading {
  color: #3498db;
}

.status-error {
  color: #e74c3c;
}

.status-success {
  color: #27ae60;
}

.chart-content {
  flex-grow: 1; /* IMPORTANTE: Crece para ocupar el espacio restante */
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0; /* IMPORTANTE: Permite que se encoja si es necesario */
  overflow: hidden; /* IMPORTANTE: Evita desbordamiento */
}

.chart-wrapper {
  position: relative;
  height: 100%; /* IMPORTANTE: Ocupa todo el alto disponible */
  width: 100%;
  min-height: 200px; /* Altura mínima razonable */
  max-height: 280px; /* IMPORTANTE: Límite máximo de altura */
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: #6c757d;
  text-align: center;
}

.error-state {
  color: #dc3545;
}

.error-state p, .loading-state p {
  margin: 0;
  font-size: 0.8rem;
}

.retry-btn {
  padding: 0.4rem 0.8rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
}

.retry-btn:hover {
  background-color: #c82333;
}

/* Responsive */
@media (max-width: 768px) {
  .individual-chart {
    padding: 0.75rem;
  }

  .chart-title h4 {
    font-size: 0.8rem;
  }

  .chart-wrapper {
    min-height: 180px;
    max-height: 250px;
  }
}
</style>
