<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<!-- Frontend/src/components/SensorsTable.vue - Simplificar completamente -->
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

// ✅ CAMBIO: Exponer la función al componente padre
defineExpose({
  fetchSensorsStatus
});
</script>

<template>
  <div class="sensors-table-container">
    <!-- Header con botón actualizar -->
    <div class="table-header">
      <h3>Estado de Sensores IoT</h3>
      <button @click="fetchSensorsStatus" class="refresh-btn" :disabled="isLoading">
        <i class="pi" :class="isLoading ? 'pi-spin pi-spinner' : 'pi-refresh'"></i>
        Actualizar
      </button>
    </div>

    <!-- Tabla siempre visible -->
    <div class="table-wrapper">
      <table class="sensors-table">
        <thead>
          <tr>
            <th>UID Sensor (MAC)</th>
            <th>Último Valor Registrado</th>
            <th>Estado</th>
            <th>Ubicación</th>
            <th>Última Lectura</th>
          </tr>
        </thead>
        <tbody>
          <!-- Estado de carga -->
          <tr v-if="isLoading">
            <td colspan="5" class="loading-cell">
              <i class="pi pi-spin pi-spinner"></i>
              Cargando datos de sensores...
            </td>
          </tr>

          <!-- Error -->
          <tr v-else-if="error">
            <td colspan="5" class="error-cell">
              <i class="pi pi-exclamation-triangle"></i>
              {{ error }}
            </td>
          </tr>

          <!-- Sin datos -->
          <tr v-else-if="sensors.length === 0">
            <td colspan="5" class="no-data-cell">
              <i class="pi pi-info-circle"></i>
              No hay sensores registrados en el sistema.
            </td>
          </tr>

          <!-- Datos de sensores -->
          <tr v-else v-for="sensor in sensors" :key="sensor.uid" class="sensor-row">
            <!-- UID -->
            <td class="sensor-uid">
              <div class="uid-container">
                <i class="pi pi-microchip"></i>
                <code>{{ sensor.uid }}</code>
              </div>
            </td>

            <!-- Último valor -->
            <td class="last-value">
              <div class="value-container">
                <span class="value">{{ sensor.last_value.value }}</span>
                <span class="unit">{{ sensor.last_value.unit }}</span>
                <div class="value-type">{{ sensor.last_value.type }}</div>
              </div>
            </td>

            <!-- Estado -->
            <td class="status">
              <div class="status-badge" :class="getStatusClass(sensor.status)">
                <i class="pi pi-circle-fill"></i>
                <span>{{ getStatusText(sensor.status) }}</span>
              </div>
              <div v-if="sensor.minutes_since_reading > 5" class="time-info">
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

.table-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
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

.table-wrapper {
  overflow-x: auto;
}

.sensors-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
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

/* Celdas especiales */
.loading-cell,
.error-cell,
.no-data-cell {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
  font-style: italic;
}

.loading-cell i {
  margin-right: 0.5rem;
}

.error-cell {
  color: #dc3545;
}

.error-cell i {
  margin-right: 0.5rem;
}

.no-data-cell i {
  margin-right: 0.5rem;
  color: #17a2b8;
}

/* Contenido de celdas */
.uid-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.uid-container i {
  color: #3498db;
}

.uid-container code {
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

.time-info {
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

/* Responsive */
@media (max-width: 992px) {
  .table-wrapper {
    overflow-x: scroll;
  }

  .sensors-table {
    min-width: 1000px;
  }
}

@media (max-width: 768px) {
  .sensors-table-container {
    padding: 1rem;
  }

  .table-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .sensors-table th,
  .sensors-table td {
    padding: 0.75rem;
  }

  .value-container .value {
    font-size: 1.25rem;
  }
}
</style>
