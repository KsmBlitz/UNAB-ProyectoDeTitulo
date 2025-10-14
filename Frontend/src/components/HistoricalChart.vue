<!-- filepath: Frontend/src/components/HistoricalChart.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
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
  Filler, // ✅ AGREGAR ESTE IMPORT
  type ChartData
} from 'chart.js';

defineOptions({
  name: 'HistoricalChart'
});

// ✅ REGISTRAR EL PLUGIN FILLER
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const props = defineProps<{
  title?: string;
  sensorType?: string;
  timeRange?: number;
}>();
const chartData = ref<ChartData<'line'>>({ labels: [], datasets: [] });
const isLoading = ref(true);
const error = ref<string | null>(null);
const timeRange = ref(props.timeRange || 24); // horas por defecto

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index' as const,
  },
  plugins: {
    legend: {
      position: 'top' as const,
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
    }
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
    },
    y: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
      },
      beginAtZero: false,
    }
  }
};

const fetchData = async () => {
  isLoading.value = true;
  error.value = null;

  const token = localStorage.getItem('userToken');

  try {
    const response = await fetch(
      `http://127.0.0.1:8000/api/charts/historical-data?sensor_type=all&hours=${timeRange.value}`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );

    if (!response.ok) {
      throw new Error('Error al cargar datos históricos');
    }

    const data = await response.json();

    const datasets = [];

    if (data.ph) {
      datasets.push({
        label: 'pH',
        data: data.ph,
        borderColor: '#e74c3c',
        backgroundColor: 'rgba(231, 76, 60, 0.1)',
        tension: 0.4,
        fill: false,
      });
    }

    if (data.temperatura) {
      datasets.push({
        label: 'Temperatura (°C)',
        data: data.temperatura,
        borderColor: '#f39c12',
        backgroundColor: 'rgba(243, 156, 18, 0.1)',
        tension: 0.4,
        fill: false,
      });
    }

    if (data.conductividad) {
      datasets.push({
        label: 'Conductividad (dS/m)',
        data: data.conductividad,
        borderColor: '#9b59b6',
        backgroundColor: 'rgba(155, 89, 182, 0.1)',
        tension: 0.4,
        fill: false,
      });
    }

    if (data.nivel_agua) {
      datasets.push({
        label: 'Nivel de Agua (m)',
        data: data.nivel_agua,
        borderColor: '#3498db',
        backgroundColor: 'rgba(52, 152, 219, 0.1)',
        tension: 0.4,
        fill: true,
      });
    }

    chartData.value = {
      labels: data.labels,
      datasets: datasets
    };

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Error desconocido';
    // Datos de ejemplo si falla
    chartData.value = {
      labels: ['10:00', '11:00', '12:00', '13:00', '14:00'],
      datasets: [
        {
          label: 'pH',
          data: [7.2, 7.1, 7.3, 7.0, 7.2],
          borderColor: '#e74c3c',
          tension: 0.4,
          fill: false,
        },
        {
          label: 'Temperatura (°C)',
          data: [22, 23, 24, 23, 22],
          borderColor: '#f39c12',
          tension: 0.4,
          fill: false,
        }
      ]
    };
  } finally {
    isLoading.value = false;
  }
};

const handleTimeRangeChange = (hours: number) => {
  timeRange.value = hours;
  fetchData();
};

onMounted(fetchData);

// Auto-refresh cada 2 minutos
setInterval(fetchData, 120000);
</script>

<template>
  <div class="chart-container">
    <div class="chart-header">
      <div class="chart-controls">
        <label>Período:</label>
        <div class="time-range-buttons">
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
            :class="{ active: timeRange === range.hours }"
            class="time-btn"
          >
            {{ range.label }}
          </button>
        </div>
      </div>
    </div>

    <div class="chart-content">
      <div v-if="error" class="error-state">
        <i class="pi pi-exclamation-triangle"></i>
        <p>{{ error }}</p>
        <button @click="fetchData" class="retry-btn">Reintentar</button>
      </div>

      <div v-else-if="isLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i>
        <p>Cargando datos históricos...</p>
      </div>

      <div v-else class="chart-wrapper">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  background-color: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.chart-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f8f9fa;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.chart-controls label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #6c757d;
}

.time-range-buttons {
  display: flex;
  gap: 0.25rem;
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 0.25rem;
}

.time-btn {
  padding: 0.5rem 1rem;
  border: none;
  background-color: transparent;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  font-size: 0.85rem;
}

.time-btn:hover {
  background-color: #e9ecef;
}

.time-btn.active {
  background-color: #3498db;
  color: white;
}

.chart-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-wrapper {
  position: relative;
  height: 400px;
  width: 100%;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #6c757d;
}

.retry-btn {
  padding: 0.5rem 1rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

/* Responsive */
@media (max-width: 768px) {
  .chart-header {
    justify-content: center;
  }

  .chart-controls {
    flex-direction: column;
    gap: 0.5rem;
  }

  .time-range-buttons {
    width: 100%;
    flex-wrap: wrap;
  }

  .time-btn {
    flex: 1;
    min-width: 60px;
  }
}
</style>
