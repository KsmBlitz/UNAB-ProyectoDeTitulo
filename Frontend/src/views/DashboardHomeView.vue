<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import MetricCard from '@/components/MetricCard.vue';
import SensorsTable from '@/components/SensorsTable.vue';
import HistoricalChartGrid from '@/components/HistoricalChartGrid.vue';
import { API_BASE_URL } from '@/config/api';  // ✅ AGREGAR IMPORT

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

// Referencias a componentes hijos
const sensorsTableRef = ref<InstanceType<typeof SensorsTable> | null>(null);
const chartsGridRef = ref<InstanceType<typeof HistoricalChartGrid> | null>(null);

// Control de auto-refresh
const isAutoRefreshEnabled = ref(true);
let refreshInterval: number | null = null;

onMounted(async () => {
  await fetchMetrics();
  startAutoRefresh();
});

// Función de refresh inteligente
async function smartRefresh() {
  // Solo actualizar métricas y tabla de sensores, NO los gráficos
  await Promise.all([
    fetchMetrics(),
    sensorsTableRef.value?.fetchSensorsStatus()
  ]);
}

// Función de refresh completo (manual)
async function fullRefresh() {
  await Promise.all([
    fetchMetrics(),
    sensorsTableRef.value?.fetchSensorsStatus(),
    chartsGridRef.value?.refreshAllCharts()
  ]);
}

function startAutoRefresh() {
  if (refreshInterval) clearInterval(refreshInterval);

  if (isAutoRefreshEnabled.value) {
    // Auto-refresh cada 30 segundos (solo métricas y sensores)
    refreshInterval = setInterval(smartRefresh, 30000);
  }
}

function toggleAutoRefresh() {
  isAutoRefreshEnabled.value = !isAutoRefreshEnabled.value;
  if (isAutoRefreshEnabled.value) {
    startAutoRefresh();
  } else if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}

async function fetchMetrics() {
  // No cambiar isLoadingMetrics si ya hay datos (para evitar parpadeo)
  const shouldShowLoading = !metrics.value;
  if (shouldShowLoading) {
    isLoadingMetrics.value = true;
  }

  errorMetrics.value = null;

  const token = localStorage.getItem('userToken');

  if (!token) {
    errorMetrics.value = "Error de autenticación. Por favor, inicia sesión nuevamente.";
    isLoadingMetrics.value = false;
    return;
  }

  try {
    // ✅ CAMBIAR URL
    const response = await fetch(`${API_BASE_URL}/api/metrics/latest`, {
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
    if (shouldShowLoading) {
      isLoadingMetrics.value = false;
    }
  }
}
</script>

<template>
  <div class="dashboard-content">
    <!-- Header con controles mejorados -->
    <header class="dashboard-header">
      <div class="header-info">
        <h1>Monitoreo del Embalse</h1>
        <p>Sistema de control de calidad del agua</p>
      </div>
      <div class="header-actions">
        <!-- Indicador de auto-refresh -->
        <div class="auto-refresh-indicator">
          <button
            @click="toggleAutoRefresh"
            class="auto-refresh-btn"
            :class="{ active: isAutoRefreshEnabled }"
          >
            <i class="pi" :class="isAutoRefreshEnabled ? 'pi-pause' : 'pi-play'"></i>
            <span>{{ isAutoRefreshEnabled ? 'Pausar' : 'Reanudar' }}</span>
          </button>
        </div>

        <!-- Botón de refresh completo -->
        <button @click="fullRefresh" class="refresh-btn">
          <i class="pi pi-refresh"></i>
          Actualizar Todo
        </button>
      </div>
    </header>

    <!-- 1. Métricas principales (Cards) -->
    <section class="metrics-section">
      <h2 class="section-title">
        <i class="pi pi-gauge"></i>
        Últimas Mediciones
        <!-- Indicador de actualización en tiempo real -->
        <span v-if="isAutoRefreshEnabled" class="live-indicator">
          <i class="pi pi-circle-fill"></i>
          EN VIVO
        </span>
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

    <!-- 2. Grid de gráficos históricos (4 gráficos) -->
    <section class="charts-section">
      <h2 class="section-title">
        <i class="pi pi-chart-line"></i>
        Tendencia Histórica por Parámetro
      </h2>
      <HistoricalChartGrid ref="chartsGridRef" />
    </section>

    <!-- 3. Tabla de sensores detallada -->
    <section class="sensors-section">
      <h2 class="section-title">
        <i class="pi pi-microchip"></i>
        Estado de Sensores IoT
      </h2>
      <SensorsTable ref="sensorsTableRef" />
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
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f8f9fa;
}

.header-info h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
}

.header-info p {
  margin: 0;
  color: #6c757d;
  font-size: 1.1rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

/* Estilos para auto-refresh */
.auto-refresh-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.auto-refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.auto-refresh-btn.active {
  background-color: #28a745;
  color: white;
  border-color: #28a745;
}

.auto-refresh-btn:hover {
  transform: translateY(-1px);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.25);
}

.refresh-btn:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #3182ce 0%, #2c5aa0 100%);
  box-shadow: 0 6px 16px rgba(49, 130, 206, 0.35);
}

/* Indicador en vivo */
.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: 1rem;
  padding: 0.25rem 0.75rem;
  background-color: rgba(40, 167, 69, 0.1);
  color: #28a745;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.live-indicator i {
  font-size: 0.5rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
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
}

.loading-shimmer {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  color: #856404;
}

.retry-btn {
  padding: 0.5rem 1rem;
  background-color: #ffc107;
  color: #212529;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  margin-left: auto;
}

.retry-btn:hover {
  background-color: #e0a800;
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-content {
    padding: 0.75rem;
  }

  .header-info h1 {
    font-size: 1.5rem;
  }

  .header-actions {
    flex-direction: column;
    gap: 0.5rem;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
