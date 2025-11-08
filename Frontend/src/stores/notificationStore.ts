import { reactive } from 'vue';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;
  timestamp: number;
}

interface NotificationStore {
  notifications: Notification[];
}

export const notificationStore = reactive<NotificationStore>({
  notifications: []
});

let notificationIdCounter = 0;

export function showNotification(
  type: NotificationType,
  title: string,
  message: string,
  duration: number = 4000
): void {
  const id = `notification-${++notificationIdCounter}-${Date.now()}`;
  
  const notification: Notification = {
    id,
    type,
    title,
    message,
    duration,
    timestamp: Date.now()
  };

  notificationStore.notifications.push(notification);

  // Auto-remove after duration
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }
}

export function removeNotification(id: string): void {
  const index = notificationStore.notifications.findIndex(n => n.id === id);
  if (index !== -1) {
    notificationStore.notifications.splice(index, 1);
  }
}

// Helper functions for common notification types
export const notify = {
  success: (title: string, message: string = '', duration?: number) => 
    showNotification('success', title, message, duration),
  
  error: (title: string, message: string = '', duration?: number) => 
    showNotification('error', title, message, duration),
  
  warning: (title: string, message: string = '', duration?: number) => 
    showNotification('warning', title, message, duration),
  
  info: (title: string, message: string = '', duration?: number) => 
    showNotification('info', title, message, duration)
};
