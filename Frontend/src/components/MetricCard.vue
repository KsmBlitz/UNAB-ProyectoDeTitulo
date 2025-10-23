<script setup lang="ts">
import { computed } from 'vue';

defineOptions({
  name: 'MetricCard'
});

const props = defineProps<{
  title: string;
  value: string;
  unit: string;
  changeText: string;
  isPositive: boolean;
  status?: 'normal' | 'warning' | 'critical';
  icon?: string;
}>();

const statusClass = computed(() => {
  switch (props.status) {
    case 'warning': return 'status-warning';
    case 'critical': return 'status-critical';
    default: return 'status-normal';
  }
});

const iconClass = computed(() => {
  if (props.icon) return props.icon;

  const title = props.title.toLowerCase();
  if (title.includes('ph')) return 'pi pi-flask';
  if (title.includes('temperatura')) return 'pi pi-sun';
  if (title.includes('conductividad')) return 'pi pi-bolt';
  if (title.includes('nivel')) return 'pi pi-chart-bar';
  return 'pi pi-circle';
});
</script>

<template>
  <div class="metric-card" :class="statusClass">
    <div class="card-header">
      <div class="title-section">
        <i :class="iconClass" class="metric-icon"></i>
        <span class="title">{{ title }}</span>
      </div>
      <div class="status-indicator" :class="statusClass">
        <i class="pi pi-circle-fill"></i>
      </div>
    </div>

    <div class="card-body">
      <div class="value-section">
        <span class="value">{{ value }}</span>
        <span class="unit">{{ unit || '' }}</span>
      </div>
    </div>

    <div class="card-footer">
      <span class="change-text">{{ changeText }}</span>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  background-color: #ffffff;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 2px solid #f8f9fa;
  min-height: 180px;
  display: flex;
  flex-direction: column;
}

/* Bordes dinámicos basados en status */
.metric-card.status-normal {
  border-color: #28a745;
}

.metric-card.status-warning {
  border-color: #ffc107;
}

.metric-card.status-critical {
  border-color: #dc3545;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.metric-icon {
  font-size: 1.25rem;
  color: #3498db;
  padding: 0.5rem;
  background-color: rgba(52, 152, 219, 0.1);
  border-radius: 50%;
}

.title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-indicator {
  font-size: 0.75rem;
}

.status-indicator.status-normal {
  color: #28a745;
}

.status-indicator.status-warning {
  color: #ffc107;
}

.status-indicator.status-critical {
  color: #dc3545;
}

.card-body {
  flex-grow: 1;
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
}

.value-section {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  width: 100%;
}

.value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  white-space: nowrap;
}

.unit {
  font-size: 1.2rem;
  font-weight: 500;
  color: #6c757d;
  min-height: 1.2rem;
  display: inline-block;
}

.card-footer {
  border-top: 1px solid #f8f9fa;
  padding-top: 1rem;
  margin-top: auto;
}

.change-text {
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
}

/* Responsive */
@media (max-width: 768px) {
  .metric-card {
    padding: 1rem;
    min-height: 160px;
  }

  .value {
    font-size: 2rem;
  }

  .unit {
    font-size: 1rem;
  }
}
</style>
