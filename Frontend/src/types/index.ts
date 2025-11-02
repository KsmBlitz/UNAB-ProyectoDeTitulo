export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  disabled: boolean;
  phone?: string;
  sms_notifications_enabled?: boolean;
  whatsapp_notifications_enabled?: boolean;
}

export interface Metric {
  value: string | number;
  unit: string;
  changeText: string;
  isPositive: boolean;
  status: 'normal' | 'warning' | 'critical';
}

export interface SensorReading {
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

export interface ChartDataPoint {
  labels: string[];
  [key: string]: number[] | string[];
}

/**
 * Alert System Types
 */
export type AlertLevel = 'info' | 'warning' | 'critical';
export type AlertType = 'ph_range' | 'conductivity' | 'temperature' | 'sensor_disconnection';
export type AlertStatus = 'active' | 'dismissed' | 'auto_resolved';

export interface ActiveAlert {
  id: string;
  type: AlertType;
  level: AlertLevel;
  title: string;
  message: string;
  value?: number;
  threshold_info: string;
  location: string;
  sensor_id: string;
  created_at: string;
  is_resolved: boolean;
}

export interface AlertSummary {
  total: number;
  critical: number;
  warning: number;
  info: number;
  has_critical: boolean;
  last_updated: string;
}

export interface AlertThresholds {
  ph: {
    optimal_min: number;
    optimal_max: number;
    warning_min: number;
    warning_max: number;
    critical_min: number;
    critical_max: number;
  };
  conductivity: {
    optimal_max: number;
    warning_max: number;
    critical_max: number;
  };
  temperature: {
    optimal_min: number;
    optimal_max: number;
    warning_min: number;
    warning_max: number;
    critical_min: number;
    critical_max: number;
  };
  sensor_timeout_warning: number;
  sensor_timeout_critical: number;
}
