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
  <div class="charts-grid-container">
    <!-- Controles de filtro temporal (compartidos por todos los gráficos) -->
    <div class="grid-header">
      <div class="grid-controls">
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
            :class="{ active: globalTimeRange === range.hours }"
            class="time-btn"
          >
            {{ range.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Grid 2x2 de gráficos individuales -->
    <div class="charts-grid">
      <!-- Fila superior -->
      <div class="chart-item">
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

      <div class="chart-item">
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
      <div class="chart-item">
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

      <div class="chart-item">
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
.charts-grid-container {
  background-color: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.grid-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f8f9fa;
}

.grid-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.grid-controls label {
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

/* Grid 2x2 con ALTURA FIJA */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 350px 350px; /* ALTURA FIJA para evitar crecimiento infinito */
  gap: 1.5rem;
}

.chart-item {
  background-color: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.chart-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

/* Responsive */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 350px); /* 4 filas de 350px cada una */
  }
}

@media (max-width: 768px) {
  .grid-header {
    justify-content: center;
  }

  .grid-controls {
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

  .charts-grid {
    gap: 1rem;
    grid-template-rows: repeat(4, 300px); /* Altura reducida en móviles */
  }
}
</style>
