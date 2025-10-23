/**
 * Umbrales para el cultivo de arándanos chilenos
 */

export interface ThresholdRange {
  optimal_min: number;
  optimal_max: number;
  warning_min: number;
  warning_max: number;
  critical_min: number;
  critical_max: number;
}

export const BLUEBERRY_THRESHOLDS = {
  ph: {
    optimal_min: 5.0,
    optimal_max: 5.5,
    warning_min: 4.5,
    warning_max: 6.0,
    critical_min: 4.0,
    critical_max: 6.5,
  },
  conductivity: {
    optimal_min: 0.0,
    optimal_max: 1.0,
    warning_min: 0.0,
    warning_max: 1.5,
    critical_min: 0.0,
    critical_max: 2.0,
  },
  temperature: {
    optimal_min: 15.0,
    optimal_max: 30.0,
    warning_min: 10.0,
    warning_max: 35.0,
    critical_min: 5.0,
    critical_max: 40.0,
  },
  water_level: {
    optimal_min: 60.0,
    optimal_max: 90.0,
    warning_min: 40.0,
    warning_max: 95.0,
    critical_min: 20.0,
    critical_max: 98.0,
  },
} as const;

export type MetricStatus = 'normal' | 'warning' | 'critical';

/**
 * Evalúa el estado de una métrica basándose en los umbrales
 */
export function evaluateMetricStatus(value: number, thresholds: ThresholdRange): MetricStatus {
  // Crítico: fuera de los límites críticos
  if (value < thresholds.critical_min || value > thresholds.critical_max) {
    return 'critical';
  }

  // Óptimo: dentro del rango óptimo
  if (value >= thresholds.optimal_min && value <= thresholds.optimal_max) {
    return 'normal';
  }

  // Advertencia: entre óptimo y crítico
  return 'warning';
}

/**
 * Obtiene la clase CSS correspondiente al estado de una métrica
 */
export function getStatusClass(status: MetricStatus): string {
  const statusClasses = {
    normal: 'status-optimal',
    warning: 'status-warning',
    critical: 'status-critical',
  };
  return statusClasses[status];
}

/**
 * Obtiene el color correspondiente al estado de una métrica
 */
export function getStatusColor(status: MetricStatus): string {
  const statusColors = {
    normal: '#28a745',
    warning: '#ffc107',
    critical: '#dc3545',
  };
  return statusColors[status];
}
