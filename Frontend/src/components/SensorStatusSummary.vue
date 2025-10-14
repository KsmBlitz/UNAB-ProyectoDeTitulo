<!-- Frontend/src/components/SensorStatusSummary.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';

defineOptions({
  name: 'SensorStatusSummary'
});

interface SensorSummary {
  summary: {
    total: number;
    online: number;
    warning: number;
    offline: number;
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sensors: any[];
  timestamp: string;
}

const summary = ref<SensorSummary | null>(null);
const isLoading = ref(true);

const fetchSummary = async () => {
  const token = localStorage.getItem('userToken');

  try {
    const response = await fetch('http://127.0.0.1:8000/api/sensors/status', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.ok) {
      summary.value = await response.json();
    }
  } catch (error) {
    console.error('Error cargando resumen de sensores:', error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchSummary);

// Auto-refresh cada 30 segundos
setInterval(fetchSummary, 30000);
</script>

<template>
  <div class="sensor-summary-container">
    <h3>Estado en Tiempo Real</h3>

    <div v-if="isLoading" class="loading">
      <i class="pi pi-spin pi-spinner"></i>
      Cargando estado...
    </div>

    <div v-else-if="summary" class="summary-grid">
      <div class="summary-card total">
        <i class="pi pi-microchip"></i>
        <span class="count">{{ summary.summary.total }}</span>
        <span class="label">Total</span>
      </div>

      <div class="summary-card online">
        <i class="pi pi-check-circle"></i>
        <span class="count">{{ summary.summary.online }}</span>
        <span class="label">Conectados</span>
      </div>

      <div class="summary-card warning">
        <i class="pi pi-exclamation-triangle"></i>
        <span class="count">{{ summary.summary.warning }}</span>
        <span class="label">Advertencia</span>
      </div>

      <div class="summary-card offline">
        <i class="pi pi-times-circle"></i>
        <span class="count">{{ summary.summary.offline }}</span>
        <span class="label">Desconectados</span>
      </div>
    </div>

    <p v-if="summary" class="last-update">
      Última actualización: {{ new Date(summary.timestamp).toLocaleTimeString('es-ES') }}
    </p>
  </div>
</template>

<style scoped>
.sensor-summary-container {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 1.5rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

.summary-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
}

.summary-card i {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.summary-card .count {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.summary-card .label {
  font-size: 0.8rem;
  text-transform: uppercase;
  font-weight: 600;
}

.total {
  background: rgba(52, 152, 219, 0.1);
  color: #3498db;
}

.online {
  background: rgba(40, 167, 69, 0.1);
  color: #28a745;
}

.warning {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.offline {
  background: rgba(220, 53, 69, 0.1);
  color: #dc3545;
}

.last-update {
  text-align: center;
  color: #6c757d;
  font-size: 0.8rem;
  margin: 0;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}
</style>
