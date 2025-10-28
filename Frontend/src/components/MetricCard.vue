<script setup lang="ts">
import { computed } from 'vue';
import { getStatusColor } from '@/utils/metrics';
import { METRIC_ICONS } from '@/utils/constants';

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

const borderColor = computed(() => getStatusColor(props.status || 'normal'));

const statusColor = computed(() => {
  switch (props.status) {
    case 'warning': return 'text-warning-500';
    case 'critical': return 'text-danger-500';
    default: return 'text-success-500';
  }
});

const iconClass = computed(() => {
  if (props.icon) return props.icon;

  const title = props.title.toLowerCase();
  if (title.includes('ph')) return METRIC_ICONS.ph;
  if (title.includes('temperatura')) return METRIC_ICONS.temperature;
  if (title.includes('conductividad')) return METRIC_ICONS.conductivity;
  if (title.includes('nivel')) return METRIC_ICONS.water_level;
  return METRIC_ICONS.default;
});
</script>

<template>
  <div
    class="bg-white rounded-xl p-6 shadow-sm transition-all duration-300 border-l-4 border-y border-r border-gray-200 min-h-[180px] flex flex-col hover:-translate-y-0.5 hover:shadow-md group"
    :style="{ borderLeftColor: borderColor }"
  >
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
          <i :class="iconClass" class="text-base text-white"></i>
        </div>
        <span class="text-sm font-semibold text-gray-700 uppercase tracking-wider">
          {{ title }}
        </span>
      </div>
      <div class="flex items-center gap-1.5">
        <i class="pi pi-circle-fill text-[6px]" :class="statusColor"></i>
        <span class="text-xs font-medium" :class="statusColor">
          {{ status === 'critical' ? 'Crítico' : status === 'warning' ? 'Alerta' : 'Normal' }}
        </span>
      </div>
    </div>

    <!-- Body -->
    <div class="flex-grow flex items-center my-4">
      <div class="flex items-baseline gap-2 w-full">
        <span class="text-3xl font-bold text-gray-900 leading-none whitespace-nowrap">
          {{ value }}
        </span>
        <span class="text-lg font-medium text-gray-500 min-h-[1.2rem] inline-block">
          {{ unit || '' }}
        </span>
      </div>
    </div>

    <!-- Footer -->
    <div class="border-t border-gray-200 pt-3 mt-auto">
      <span class="text-xs text-gray-600">
        {{ changeText }}
      </span>
    </div>
  </div>
</template>

<!-- Todos los estilos ahora son manejados por Tailwind CSS -->
