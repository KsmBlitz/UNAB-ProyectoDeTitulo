<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';

defineOptions({
  name: 'SensorsTable'
});

interface SensorReading {
  uid: string;
  last_value: {
    value: number;
    unit: string;
    type: string;
  };
  status: 'online' | 'offline' | 'warning';
  location: string;
  last_reading: string;
  minutes_since_reading: number;
}

const sensors = ref<SensorReading[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const fetchSensorsStatus = async () => {
  isLoading.value = true;
  error.value = null;

  const token = localStorage.getItem('userToken');

  try {
    const response = await fetch('http://127.0.0.1:8000/api/sensors/individual', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      throw new Error('Error al cargar estado de sensores');
    }

    const sensorsData = await response.json();

    // Mapear datos del backend
    sensors.value = sensorsData.map((sensor: any) => ({
      uid: sensor.uid,
      last_value: sensor.last_value,
      status: sensor.status,
      location: sensor.location,
      last_reading: sensor.last_reading,
      minutes_since_reading: sensor.minutes_since_reading
    }));

  } catch (err) {
    console.error('Error al cargar sensores:', err);
    error.value = 'No se pudieron cargar los datos de sensores.';
  } finally {
    isLoading.value = false;
  }
};

const formatLastReading = (isoString: string) => {
  const date = new Date(isoString);
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'online': return 'Conectado';
    case 'warning': return 'Advertencia';
    case 'offline': return 'Desconectado';
    default: return 'Desconocido';
  }
};

const getStatusClass = (status: string) => {
  switch (status) {
    case 'online': return 'status-online';
    case 'warning': return 'status-warning';
    case 'offline': return 'status-offline';
    default: return 'status-unknown';
  }
};

onMounted(fetchSensorsStatus);

// Auto-refresh cada 30 segundos
setInterval(fetchSensorsStatus, 30000);

// Exponer la función al componente padre
defineExpose({
  fetchSensorsStatus
});
</script>

<template>
  <div class="sensors-table-container">
    <!-- Header con botón actualizar -->
    <div class="table-header">
      <div class="sensors-summary">
        <div class="summary-item">
          <span class="count">{{ sensors.filter(s => s.status === 'online').length }}</span>
          <span class="label">Conectados</span>
        </div>
        <div class="summary-item warning">
          <span class="count">{{ sensors.filter(s => s.status === 'warning').length }}</span>
          <span class="label">Advertencia</span>
        </div>
        <div class="summary-item offline">
          <span class="count">{{ sensors.filter(s => s.status === 'offline').length }}</span>
          <span class="label">Desconectados</span>
        </div>
      </div>
      <button @click="fetchSensorsStatus" class="refresh-btn" :disabled="isLoading">
        <i class="pi" :class="isLoading ? 'pi-spin pi-spinner' : 'pi-refresh'"></i>
        Actualizar
      </button>
    </div>

    <div v-if="error" class="error-state">
      <i class="pi pi-info-circle"></i>
      <p>{{ error }}</p>
    </div>

    <div v-if="isLoading" class="loading-state">
      <i class="pi pi-spin pi-spinner"></i>
      Cargando estado de sensores...
    </div>

    <!-- Vista de tabla para desktop -->
    <div v-else class="table-wrapper desktop-view">
      <table class="sensors-table">
        <thead>
          <tr>
            <th>UID Sensor (MAC)</th>
            <th>Últimos Valores Registrados</th>
            <th>Estado</th>
            <th>Ubicación</th>
            <th>Última Lectura</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sensor in sensors" :key="sensor.uid" class="sensor-row">
            <!-- UID/MAC -->
            <td class="sensor-uid">
              <div class="uid-info">
                <i class="pi pi-microchip"></i>
                <code>{{ sensor.uid }}</code>
              </div>
            </td>

            <!-- Últimos valores -->
            <td class="sensor-values">
              <div class="value-container">
                <span class="value">{{ sensor.last_value.value }}</span>
                <span class="unit">{{ sensor.last_value.unit }}</span>
                <div class="value-type">{{ sensor.last_value.type }}</div>
              </div>
            </td>

            <!-- Estado -->
            <td>
              <div class="status-badge" :class="getStatusClass(sensor.status)">
                <i class="pi pi-circle-fill"></i>
                <span>{{ getStatusText(sensor.status) }}</span>
              </div>
              <div v-if="sensor.minutes_since_reading > 0" class="inactive-time">
                {{ sensor.minutes_since_reading }} min sin datos
              </div>
            </td>

            <!-- Ubicación -->
            <td class="location">
              <i class="pi pi-map-marker"></i>
              {{ sensor.location }}
            </td>

            <!-- Última lectura -->
            <td class="last-reading">
              {{ formatLastReading(sensor.last_reading) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Vista de cards para móviles -->
    <div class="mobile-view">
      <div class="sensors-grid">
        <div v-for="sensor in sensors" :key="sensor.uid" class="sensor-card" :class="`card-${sensor.status}`">
          <div class="card-header">
            <div class="sensor-uid-mobile">
              <i class="pi pi-microchip"></i>
              <code>{{ sensor.uid }}</code>
            </div>
            <div class="status-badge" :class="getStatusClass(sensor.status)">
              <i class="pi pi-circle-fill"></i>
            </div>
          </div>

          <div class="card-body">
            <div class="values-mobile">
              <div class="value-row">
                <span>{{ sensor.last_value.type }}: <strong>{{ sensor.last_value.value }} {{ sensor.last_value.unit }}</strong></span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <div class="info-item">
              <i class="pi pi-clock"></i>
              {{ formatLastReading(sensor.last_reading) }}
            </div>
            <div class="info-item">
              <i class="pi pi-map-marker"></i>
              {{ sensor.location }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sensors-table-container {
  background-color: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f8f9fa;
}

.sensors-summary {
  display: flex;
  gap: 2rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.summary-item .count {
  font-size: 1.5rem;
  font-weight: 700;
  color: #28a745;
}

.summary-item.warning .count {
  color: #ffc107;
}

.summary-item.offline .count {
  color: #dc3545;
}

.summary-item .label {
  font-size: 0.8rem;
  color: #6c757d;
  text-transform: uppercase;
  font-weight: 600;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #e9ecef;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 3rem;
  color: #6c757d;
}

.error-state {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background-color: #e3f2fd;
  border-radius: 6px;
  color: #1565c0;
  margin-bottom: 1rem;
}

/* Vista desktop */
.desktop-view {
  display: block;
}

.mobile-view {
  display: none;
}

.sensors-table {
  width: 100%;
  border-collapse: collapse;
}

.sensors-table th {
  text-align: left;
  padding: 1rem;
  font-weight: 600;
  color: #6c757d;
  font-size: 0.9rem;
  text-transform: uppercase;
  border-bottom: 2px solid #f8f9fa;
  background-color: #f8f9fa;
}

.sensors-table td {
  padding: 1rem;
  border-bottom: 1px solid #f8f9fa;
  vertical-align: middle;
}

.sensor-row:hover {
  background-color: rgba(52, 152, 219, 0.05);
}

.uid-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.uid-info i {
  color: #3498db;
}

.uid-info code {
  font-family: 'Monaco', 'Menlo', monospace;
  background-color: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.value-container {
  text-align: center;
}

.value-container .value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
}

.value-container .unit {
  font-size: 1rem;
  color: #6c757d;
  margin-left: 0.25rem;
}

.value-container .value-type {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
  text-transform: uppercase;
  font-weight: 500;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-online {
  background-color: rgba(40, 167, 69, 0.1);
  color: #28a745;
}

.status-warning {
  background-color: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.status-offline {
  background-color: rgba(220, 53, 69, 0.1);
  color: #dc3545;
}

.status-unknown {
  background-color: rgba(108, 117, 125, 0.1);
  color: #6c757d;
}

.inactive-time {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.location {
  color: #6c757d;
}

.location i {
  margin-right: 0.5rem;
  color: #dc3545;
}

.last-reading {
  color: #6c757d;
  font-size: 0.9rem;
}

/* Vista móvil */
@media (max-width: 992px) {
  .desktop-view {
    display: none;
  }

  .mobile-view {
    display: block;
  }

  .sensors-grid {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }

  .sensor-card {
    border: 2px solid #e9ecef;
    border-radius: 8px;
    padding: 1rem;
    background-color: #fff;
    transition: all 0.2s;
  }

  .sensor-card.card-online {
    border-left-color: #28a745;
  }

  .sensor-card.card-warning {
    border-left-color: #ffc107;
  }

  .sensor-card.card-offline {
    border-left-color: #dc3545;
  }

  .sensor-card .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .sensor-uid-mobile {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .sensor-uid-mobile code {
    font-family: 'Monaco', 'Menlo', monospace;
    background-color: #f8f9fa;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .values-mobile {
    margin-bottom: 1rem;
  }

  .value-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .sensor-card .card-footer {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #6c757d;
  }

  .info-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
}

/* Pantallas muy pequeñas */
@media (max-width: 576px) {
  .sensors-table-container {
    padding: 1rem;
  }

  .table-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .sensors-summary {
    justify-content: space-around;
  }

  .sensors-grid {
    grid-template-columns: 1fr;
  }

  .sensor-card .card-footer {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
