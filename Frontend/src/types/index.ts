export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  disabled: boolean;
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
