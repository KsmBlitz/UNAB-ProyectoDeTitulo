<script setup lang="ts">
import { ref, onMounted } from 'vue';
import MetricCard from '@/components/MetricCard.vue';
import SensorsTable from '@/components/SensorsTable.vue';
import HistoricalChart from '@/components/HistoricalChart.vue';

defineOptions({
  name: 'DashboardHomeView'
});

interface MetricData {
  value: number;
  unit: string;
  changeText: string;
  isPositive: boolean;
  status: 'normal' | 'warning' | 'critical';
}

interface Metrics {
  temperatura_agua: MetricData;
  ph: MetricData;
  conductividad: MetricData;
  nivel_agua: MetricData;
}

// Estados para métricas
const metrics = ref<Metrics | null>(null);
const errorMetrics = ref<string | null>(null);
const isLoadingMetrics = ref(true);

onMounted(async () => {
  await fetchMetrics();
  // Auto-refresh cada 30 segundos
  setInterval(fetchMetrics, 30000);
});

async function fetchMetrics() {
  isLoadingMetrics.value = true;
  errorMetrics.value = null;

  const token = localStorage.getItem('userToken');

  if (!token) {
    errorMetrics.value = "Error de autenticación. Por favor, inicia sesión nuevamente.";
    isLoadingMetrics.value = false;
    return;
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/api/metrics/latest', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('No hay mediciones disponibles en este momento.');
      } else if (response.status === 401) {
        throw new Error('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
      } else {
        throw new Error(`Error del servidor (${response.status}). Las mediciones pueden tardar hasta 5 minutos en actualizarse.`);
      }
    }

    metrics.value = await response.json();
  } catch (e) {
    console.error('Error al cargar métricas:', e);
    if (e instanceof Error) {
      errorMetrics.value = e.message;
    } else {
      errorMetrics.value = "Error al cargar las métricas. Intenta actualizar la página.";
    }
  } finally {
    isLoadingMetrics.value = false;
  }
}

function refreshAll() {
  fetchMetrics();
}
</script>

<template>
  <div class="dashboard-content">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-info">
        <h1>Monitoreo del Embalse</h1>
        <p>Sistema de control de calidad del agua</p>
      </div>
      <div class="header-actions">
        <button @click="refreshAll" class="refresh-btn">
          <i class="pi pi-refresh"></i>
          Actualizar
        </button>
      </div>
    </header>

    <!-- 1. Métricas principales (Cards) -->
    <section class="metrics-section">
      <h2 class="section-title">
        <i class="pi pi-gauge"></i>
        Últimas Mediciones
      </h2>

      <div v-if="errorMetrics" class="error-message">
        <i class="pi pi-exclamation-triangle"></i>
        {{ errorMetrics }}
        <button @click="fetchMetrics" class="retry-btn">Reintentar</button>
      </div>

      <div v-else-if="isLoadingMetrics" class="loading-state">
        <div class="loading-cards">
          <div v-for="i in 4" :key="i" class="loading-card">
            <div class="loading-shimmer"></div>
          </div>
        </div>
      </div>

      <div v-else-if="metrics" class="metrics-grid">
        <MetricCard
          title="Temperatura del Agua"
          :value="String(metrics.temperatura_agua.value)"
          :unit="metrics.temperatura_agua.unit"
          :changeText="metrics.temperatura_agua.changeText"
          :isPositive="metrics.temperatura_agua.isPositive"
          :status="metrics.temperatura_agua.status"
          icon="pi pi-sun"
        />

        <MetricCard
          title="Nivel de pH"
          :value="String(metrics.ph.value)"
          :unit="metrics.ph.unit"
          :changeText="metrics.ph.changeText"
          :isPositive="metrics.ph.isPositive"
          :status="metrics.ph.status"
          icon="pi pi-flask"
        />

        <MetricCard
          title="Conductividad Eléctrica"
          :value="String(metrics.conductividad.value)"
          :unit="metrics.conductividad.unit"
          :changeText="metrics.conductividad.changeText"
          :isPositive="metrics.conductividad.isPositive"
          :status="metrics.conductividad.status"
          icon="pi pi-bolt"
        />

        <MetricCard
          title="Nivel del Agua"
          :value="String(metrics.nivel_agua.value)"
          :unit="metrics.nivel_agua.unit"
          :changeText="metrics.nivel_agua.changeText"
          :isPositive="metrics.nivel_agua.isPositive"
          :status="metrics.nivel_agua.status"
          icon="pi pi-chart-bar"
        />
      </div>
    </section>

    <!-- 2. AGREGAR: Gráfico histórico -->
    <section class="charts-section">
      <h2 class="section-title">
        <i class="pi pi-chart-line"></i>
        Tendencia Histórica
      </h2>
      <HistoricalChart
        title="Mediciones Históricas"
        sensorType="all"
        :timeRange="24"
      />
    </section>

    <!-- 3. Tabla de sensores -->
    <section class="sensors-section">
      <h2 class="section-title">
        <i class="pi pi-microchip"></i>
        Estado de Sensores IoT
      </h2>
      <SensorsTable />
    </section>
  </div>
</template>

<style scoped>
.dashboard-content {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #e9ecef;
}

.header-info h1 {
  font-size: 2.25rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.header-info p {
  font-size: 1.1rem;
  color: #6c757d;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(52, 152, 219, 0.3);
}

.metrics-section, .sensors-section, .charts-section {
  margin-bottom: 2rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.4rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1.5rem;
}

.section-title i {
  color: #3498db;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.loading-state {
  padding: 2rem 0;
}

.loading-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.loading-card {
  height: 140px;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  background-color: #f8f9fa;
}

.loading-shimmer {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #f8f9fa 25%, #e9ecef 50%, #f8f9fa 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.error-message {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  color: #721c24;
}

.retry-btn {
  padding: 0.25rem 0.75rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.retry-btn:hover {
  background-color: #c82333;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .dashboard-content {
    padding: 1rem;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-info h1 {
    font-size: 1.8rem;
  }

  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }
}

@media (max-width: 576px) {
  .dashboard-content {
    padding: 0.75rem;
  }

  .header-info h1 {
    font-size: 1.5rem;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
