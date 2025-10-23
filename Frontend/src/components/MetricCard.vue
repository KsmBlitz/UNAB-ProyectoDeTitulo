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
    class="bg-white rounded-card p-6 shadow-card transition-all duration-300 border-2 min-h-[180px] flex flex-col hover:-translate-y-0.5 hover:shadow-card-hover"
    :style="{ borderColor }"
  >
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-center gap-3">
        <i
          :class="iconClass"
          class="text-xl text-primary-500 p-2 bg-primary-50 rounded-full"
        ></i>
        <span class="text-sm font-semibold text-gray-600 uppercase tracking-wide">
          {{ title }}
        </span>
      </div>
      <div class="text-xs" :class="statusColor">
        <i class="pi pi-circle-fill"></i>
      </div>
    </div>

    <!-- Body -->
    <div class="flex-grow flex items-center my-6">
      <div class="flex items-baseline gap-2 w-full">
        <span class="text-4xl font-bold text-gray-800 leading-none whitespace-nowrap">
          {{ value }}
        </span>
        <span class="text-xl font-medium text-gray-600 min-h-[1.2rem] inline-block">
          {{ unit || '' }}
        </span>
      </div>
    </div>

    <!-- Footer -->
    <div class="border-t border-gray-100 pt-4 mt-auto">
      <span class="text-sm text-gray-600 font-medium">
        {{ changeText }}
      </span>
    </div>
  </div>
</template>

<!-- Todos los estilos ahora son manejados por Tailwind CSS -->
