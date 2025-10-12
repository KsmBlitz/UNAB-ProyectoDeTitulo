<script setup lang="ts">
import { ref, onMounted } from 'vue';

defineOptions({
  name: 'SensorsTable'
});

interface IndividualSensor {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'warning';
  last_reading: string;
  current_value: number;
  unit: string;
  location: string;
  signal_strength: number; // 0-100
  battery_level?: number;  // 0-100 (opcional)
  uid: string;
}

const sensors = ref<IndividualSensor[]>([]);
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

    sensors.value = await response.json();
  } catch (err) {
    console.error('Error al cargar sensores:', err);
    error.value = 'Error al cargar datos. Mostrando información de ejemplo.';

    // Datos de ejemplo más realistas con sensores individuales
    sensors.value = [
      {
        id: "SNR-001",
        name: "Sensor pH Principal",
        type: "pH",
        status: "online",
        last_reading: new Date().toISOString(),
        current_value: 7.2,
        unit: "pH",
        location: "Sector A - Entrada",
        signal_strength: 95,
        battery_level: 78,
        uid: "251-661-5362"
      },
      {
        id: "SNR-002",
        name: "Sensor pH Secundario",
        type: "pH",
        status: "online",
        last_reading: new Date(Date.now() - 300000).toISOString(), // 5 min ago
        current_value: 7.0,
        unit: "pH",
        location: "Sector B - Centro",
        signal_strength: 87,
        battery_level: 65,
        uid: "251-661-5363"
      },
      {
        id: "SNR-003",
        name: "Sensor Temperatura T1",
        type: "temperatura",
        status: "online",
        last_reading: new Date().toISOString(),
        current_value: 22.5,
        unit: "°C",
        location: "Sector A - Superficie",
        signal_strength: 92,
        battery_level: 82,
        uid: "171-534-1262"
      },
      {
        id: "SNR-004",
        name: "Sensor Temperatura T2",
        type: "temperatura",
        status: "warning",
        last_reading: new Date(Date.now() - 1800000).toISOString(), // 30 min ago
        current_value: 24.1,
        unit: "°C",
        location: "Sector B - Profundo",
        signal_strength: 45,
        battery_level: 23,
        uid: "171-534-1263"
      },
      {
        id: "SNR-005",
        name: "Sensor Conductividad EC1",
        type: "conductividad",
        status: "online",
        last_reading: new Date().toISOString(),
        current_value: 1.8,
        unit: "dS/m",
        location: "Sector A - Centro",
        signal_strength: 89,
        battery_level: 71,
        uid: "334-892-7721"
      },
      {
        id: "SNR-006",
        name: "Sensor Nivel NV1",
        type: "nivel",
        status: "offline",
        last_reading: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        current_value: 2.3,
        unit: "m",
        location: "Sector C - Salida",
        signal_strength: 0,
        battery_level: 5,
        uid: "445-123-9981"
      },
      {
        id: "SNR-007",
        name: "Sensor Nivel NV2",
        type: "nivel",
        status: "online",
        last_reading: new Date().toISOString(),
        current_value: 2.1,
        unit: "m",
        location: "Sector A - Entrada",
        signal_strength: 93,
        battery_level: 88,
        uid: "445-123-9982"
      }
    ];
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

const getSignalIcon = (strength: number) => {
  if (strength >= 80) return 'pi pi-wifi';
  if (strength >= 60) return 'pi pi-wifi';
  if (strength >= 40) return 'pi pi-wifi';
  if (strength >= 20) return 'pi pi-wifi';
  return 'pi pi-wifi';
};

const getSignalClass = (strength: number) => {
  if (strength >= 80) return 'signal-excellent';
  if (strength >= 60) return 'signal-good';
  if (strength >= 40) return 'signal-fair';
  if (strength >= 20) return 'signal-poor';
  return 'signal-none';
};

const getBatteryClass = (level?: number) => {
  if (!level) return 'battery-unknown';
  if (level >= 60) return 'battery-good';
  if (level >= 30) return 'battery-medium';
  if (level >= 10) return 'battery-low';
  return 'battery-critical';
};

onMounted(fetchSensorsStatus);

// Auto-refresh cada 30 segundos
setInterval(fetchSensorsStatus, 30000);
</script>

<template>
  <div class="sensors-table-container">
    <div class="table-header">
      <div class="sensors-summary">
        <div class="summary-item">
          <span class="count">{{ sensors.filter(s => s.status === 'online').length }}</span>
          <span class="label">En línea</span>
        </div>
        <div class="summary-item warning">
          <span class="count">{{ sensors.filter(s => s.status === 'warning').length }}</span>
          <span class="label">Advertencia</span>
        </div>
        <div class="summary-item offline">
          <span class="count">{{ sensors.filter(s => s.status === 'offline').length }}</span>
          <span class="label">Desconectado</span>
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
            <th>Sensor</th>
            <th>ID/UID</th>
            <th>Valor Actual</th>
            <th>Estado</th>
            <th>Señal</th>
            <th>Batería</th>
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
            <td class="sensor-id">
              <div class="id-info">
                <div class="sensor-id-main">{{ sensor.id }}</div>
                <div class="sensor-uid">{{ sensor.uid }}</div>
              </div>
            </td>
            <td class="sensor-value">
              <span class="value">{{ sensor.current_value }}</span>
              <span class="unit">{{ sensor.unit }}</span>
            </td>
            <td>
              <div class="status-badge" :class="`status-${sensor.status}`">
                <i class="pi pi-circle-fill"></i>
                {{ sensor.status === 'online' ? 'En línea' :
                   sensor.status === 'warning' ? 'Advertencia' : 'Desconectado' }}
              </div>
            </td>
            <td class="signal-info">
              <div class="signal-indicator" :class="getSignalClass(sensor.signal_strength)">
                <i :class="getSignalIcon(sensor.signal_strength)"></i>
                <span>{{ sensor.signal_strength }}%</span>
              </div>
            </td>
            <td class="battery-info">
              <div v-if="sensor.battery_level" class="battery-indicator" :class="getBatteryClass(sensor.battery_level)">
                <i class="pi pi-bolt"></i>
                <span>{{ sensor.battery_level }}%</span>
              </div>
              <span v-else class="no-battery">N/A</span>
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
    </div>

    <!-- Vista de cards para móviles -->
    <div class="mobile-view">
      <div class="sensors-grid">
        <div v-for="sensor in sensors" :key="sensor.id" class="sensor-card" :class="`card-${sensor.status}`">
          <div class="card-header">
            <div class="sensor-info">
              <i :class="getSensorIcon(sensor.type)" class="sensor-icon"></i>
              <div>
                <div class="sensor-name">{{ sensor.name }}</div>
                <div class="sensor-type">{{ sensor.type }} • {{ sensor.id }}</div>
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
            <div class="sensor-metrics">
              <div class="metric">
                <i :class="[getSignalIcon(sensor.signal_strength), getSignalClass(sensor.signal_strength)]"></i>
                <span>{{ sensor.signal_strength }}%</span>
              </div>
              <div v-if="sensor.battery_level" class="metric">
                <i class="pi pi-bolt"></i>
                <span>{{ sensor.battery_level }}%</span>
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

.sensor-id-main {
  font-weight: 600;
  color: #2c3e50;
  font-family: monospace;
}

.sensor-uid {
  font-size: 0.8rem;
  color: #6c757d;
  font-family: monospace;
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

.status-warning {
  background-color: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.status-offline {
  background-color: rgba(220, 53, 69, 0.1);
  color: #dc3545;
}

.signal-indicator, .battery-indicator {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
}

.signal-excellent {
  color: #28a745;
}

.signal-good {
  color: #6c757d;
}

.signal-fair {
  color: #ffc107;
}

.signal-poor {
  color: #fd7e14;
}

.signal-none {
  color: #dc3545;
}

.battery-good {
  color: #28a745;
}

.battery-medium {
  color: #ffc107;
}

.battery-low {
  color: #fd7e14;
}

.battery-critical {
  color: #dc3545;
}

.no-battery {
  color: #6c757d;
  font-size: 0.8rem;
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

  .sensor-card .card-body {
    margin-bottom: 1rem;
  }

  .sensor-metrics {
    display: flex;
    gap: 1rem;
    margin-top: 0.5rem;
  }

  .metric {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.8rem;
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
