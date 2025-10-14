<!-- filepath: Frontend/src/components/SensorsStatusTable.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue';

defineOptions({
  name: 'SensorsStatusTable'
});

interface Sensor {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline';
  last_reading: string;
  current_value: number;
  unit: string;
  location: string;
}

const sensors = ref<Sensor[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const fetchSensorsStatus = async () => {
  isLoading.value = true;
  error.value = null;

  const token = localStorage.getItem('userToken');

  try {
    const response = await fetch('http://127.0.0.1:8000/api/sensors/status', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      throw new Error('Error al cargar estado de sensores');
    }

    sensors.value = await response.json();
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Error desconocido';
  } finally {
    isLoading.value = false;
  }
};

const formatLastReading = (isoString: string) => {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffMinutes < 1) return 'Ahora mismo';
  if (diffMinutes < 60) return `Hace ${diffMinutes} min`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `Hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;

  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getSensorIcon = (type: string) => {
  const icons = {
    'pH': 'pi pi-flask',
    'temperatura': 'pi pi-sun',
    'conductividad': 'pi pi-bolt',
    'nivel': 'pi pi-chart-bar'
  };
  return icons[type as keyof typeof icons] || 'pi pi-circle';
};

onMounted(fetchSensorsStatus);

// Auto-refresh cada 30 segundos
setInterval(fetchSensorsStatus, 30000);
</script>

<template>
  <div class="sensors-table-container">
    <div class="table-header">
      <h3>Estado de Sensores</h3>
      <button @click="fetchSensorsStatus" class="refresh-btn" :disabled="isLoading">
        <i class="pi" :class="isLoading ? 'pi-spin pi-spinner' : 'pi-refresh'"></i>
        Actualizar
      </button>
    </div>

    <div v-if="error" class="error-state">
      <i class="pi pi-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="fetchSensorsStatus" class="retry-btn">Reintentar</button>
    </div>

    <div v-else class="table-wrapper">
      <!-- Vista de tabla para pantallas grandes -->
      <table class="sensors-table desktop-table">
        <thead>
          <tr>
            <th>Sensor</th>
            <th>Valor Actual</th>
            <th>Estado</th>
            <th>Última Lectura</th>
            <th>Ubicación</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sensor in sensors" :key="sensor.id" class="sensor-row">
            <td class="sensor-info">
              <div class="sensor-details">
                <i :class="getSensorIcon(sensor.type)" class="sensor-icon"></i>
                <div>
                  <div class="sensor-name">{{ sensor.name }}</div>
                  <div class="sensor-type">{{ sensor.type }}</div>
                </div>
              </div>
            </td>
            <td class="sensor-value">
              <span class="value">{{ sensor.current_value }}</span>
              <span class="unit">{{ sensor.unit }}</span>
            </td>
            <td>
              <div class="status-badge" :class="`status-${sensor.status}`">
                <i class="pi pi-circle-fill"></i>
                {{ sensor.status === 'online' ? 'En línea' : 'Desconectado' }}
              </div>
            </td>
            <td class="last-reading">
              {{ formatLastReading(sensor.last_reading) }}
            </td>
            <td class="location">
              <i class="pi pi-map-marker"></i>
              {{ sensor.location }}
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Vista de cards para pantallas pequeñas -->
      <div class="sensors-cards mobile-cards">
        <div v-for="sensor in sensors" :key="sensor.id" class="sensor-card">
          <div class="card-header">
            <div class="sensor-info">
              <i :class="getSensorIcon(sensor.type)" class="sensor-icon"></i>
              <div>
                <div class="sensor-name">{{ sensor.name }}</div>
                <div class="sensor-type">{{ sensor.type }}</div>
              </div>
            </div>
            <div class="status-badge" :class="`status-${sensor.status}`">
              <i class="pi pi-circle-fill"></i>
            </div>
          </div>

          <div class="card-body">
            <div class="sensor-value">
              <span class="value">{{ sensor.current_value }}</span>
              <span class="unit">{{ sensor.unit }}</span>
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

/* Vista de tabla (desktop) */
.desktop-table {
  display: table;
  width: 100%;
}

.mobile-cards {
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
}

.sensors-table td {
  padding: 1rem;
  border-bottom: 1px solid #f8f9fa;
  vertical-align: middle;
}

.sensor-row:hover {
  background-color: #f8f9fa;
}

.sensor-details {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sensor-icon {
  font-size: 1.25rem;
  color: #3498db;
  padding: 0.5rem;
  background-color: rgba(52, 152, 219, 0.1);
  border-radius: 50%;
}

.sensor-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.sensor-type {
  font-size: 0.8rem;
  color: #6c757d;
  text-transform: capitalize;
}

.sensor-value {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.sensor-value .value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.sensor-value .unit {
  font-size: 0.9rem;
  color: #6c757d;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-online {
  background-color: rgba(40, 167, 69, 0.1);
  color: #28a745;
}

.status-offline {
  background-color: rgba(220, 53, 69, 0.1);
  color: #dc3545;
}

.last-reading {
  color: #6c757d;
  font-size: 0.9rem;
}

.location {
  color: #6c757d;
  font-size: 0.9rem;
}

.location i {
  margin-right: 0.25rem;
}

/* Vista móvil */
@media (max-width: 992px) {
  .desktop-table {
    display: none;
  }

  .mobile-cards {
    display: block;
  }

  .sensors-cards {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }

  .sensor-card {
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 1rem;
    background-color: #fff;
  }

  .sensor-card .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .sensor-card .card-body {
    margin-bottom: 1rem;
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

  .sensors-cards {
    grid-template-columns: 1fr;
  }

  .table-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .sensor-card .card-footer {
    flex-direction: column;
    gap: 0.5rem;
  }
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #6c757d;
}

.error-state i {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #dc3545;
}

.retry-btn {
  padding: 0.5rem 1rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 1rem;
}

.retry-btn:hover {
  background-color: #c82333;
}
</style>
