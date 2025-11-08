<script setup lang="ts">
import { computed } from 'vue';
import { notificationStore, removeNotification, type Notification } from '@/stores/notificationStore';

defineOptions({
  name: 'NotificationToast'
});

const notifications = computed(() => notificationStore.notifications);

const getIcon = (type: string): string => {
  switch (type) {
    case 'success': return 'pi-check-circle';
    case 'error': return 'pi-times-circle';
    case 'warning': return 'pi-exclamation-triangle';
    case 'info': return 'pi-info-circle';
    default: return 'pi-info-circle';
  }
};

const getColors = (type: string) => {
  switch (type) {
    case 'success':
      return {
        bg: 'bg-green-50',
        border: 'border-green-500',
        icon: 'text-green-600',
        title: 'text-green-900',
        message: 'text-green-700'
      };
    case 'error':
      return {
        bg: 'bg-red-50',
        border: 'border-red-500',
        icon: 'text-red-600',
        title: 'text-red-900',
        message: 'text-red-700'
      };
    case 'warning':
      return {
        bg: 'bg-yellow-50',
        border: 'border-yellow-500',
        icon: 'text-yellow-600',
        title: 'text-yellow-900',
        message: 'text-yellow-700'
      };
    case 'info':
      return {
        bg: 'bg-blue-50',
        border: 'border-blue-500',
        icon: 'text-blue-600',
        title: 'text-blue-900',
        message: 'text-blue-700'
      };
    default:
      return {
        bg: 'bg-gray-50',
        border: 'border-gray-500',
        icon: 'text-gray-600',
        title: 'text-gray-900',
        message: 'text-gray-700'
      };
  }
};

const dismiss = (notification: Notification) => {
  removeNotification(notification.id);
};
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-20 right-6 z-[9999] flex flex-col gap-3 pointer-events-none max-w-md">
      <TransitionGroup name="notification">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="[
            'pointer-events-auto rounded-xl shadow-2xl border-l-4 p-4 flex items-start gap-3',
            'backdrop-blur-sm bg-white/95 transform transition-all duration-300',
            'hover:scale-105 hover:shadow-3xl',
            getColors(notification.type).border
          ]"
        >
          <!-- Icon -->
          <div class="flex-shrink-0">
            <i
              :class="['pi text-xl', getIcon(notification.type), getColors(notification.type).icon]"
            ></i>
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <h4
              :class="['font-semibold text-sm mb-1', getColors(notification.type).title]"
            >
              {{ notification.title }}
            </h4>
            <p
              v-if="notification.message"
              :class="['text-xs leading-relaxed', getColors(notification.type).message]"
            >
              {{ notification.message }}
            </p>
          </div>

          <!-- Close Button -->
          <button
            @click="dismiss(notification)"
            class="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
            title="Cerrar"
          >
            <i class="pi pi-times text-sm"></i>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.notification-enter-active {
  animation: slideInRight 0.3s ease-out;
}

.notification-leave-active {
  animation: slideOutRight 0.3s ease-in;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOutRight {
  from {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateX(100%) scale(0.9);
  }
}
</style>
