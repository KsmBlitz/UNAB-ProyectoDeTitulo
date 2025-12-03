import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { authStore } from '@/auth/store';
import { notify } from '@/stores/notificationStore';

// Tiempo de inactividad antes de mostrar advertencia (en ms)
const INACTIVITY_TIMEOUT = 15 * 60 * 1000; // 15 minutos

// Tiempo adicional después de la advertencia antes de cerrar sesión (en ms)
const WARNING_TIMEOUT = 60 * 1000; // 1 minuto

// Eventos que reinician el timer de inactividad
const ACTIVITY_EVENTS = [
  'mousedown',
  'mousemove',
  'keydown',
  'scroll',
  'touchstart',
  'click',
  'wheel'
];

export function useInactivityLogout() {
  const router = useRouter();
  
  const showWarningModal = ref(false);
  const secondsRemaining = ref(WARNING_TIMEOUT / 1000);
  
  let inactivityTimer: ReturnType<typeof setTimeout> | null = null;
  let warningTimer: ReturnType<typeof setTimeout> | null = null;
  let countdownInterval: ReturnType<typeof setInterval> | null = null;

  /**
   * Cierra la sesión del usuario
   */
  const logout = () => {
    cleanup();
    authStore.user = null;
    localStorage.removeItem('userToken');
    notify.warning('Sesión cerrada', 'Tu sesión ha sido cerrada por inactividad.');
    router.push('/login');
  };

  /**
   * Limpia todos los timers
   */
  const cleanup = () => {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
      inactivityTimer = null;
    }
    if (warningTimer) {
      clearTimeout(warningTimer);
      warningTimer = null;
    }
    if (countdownInterval) {
      clearInterval(countdownInterval);
      countdownInterval = null;
    }
    showWarningModal.value = false;
  };

  /**
   * Inicia el countdown de la advertencia
   */
  const startWarningCountdown = () => {
    secondsRemaining.value = WARNING_TIMEOUT / 1000;
    
    countdownInterval = setInterval(() => {
      secondsRemaining.value--;
      if (secondsRemaining.value <= 0) {
        logout();
      }
    }, 1000);
  };

  /**
   * Muestra la advertencia de inactividad
   */
  const showWarning = () => {
    showWarningModal.value = true;
    startWarningCountdown();
    
    // Timer para cerrar sesión después del tiempo de advertencia
    warningTimer = setTimeout(() => {
      logout();
    }, WARNING_TIMEOUT);
  };

  /**
   * Reinicia el timer de inactividad
   */
  const resetInactivityTimer = () => {
    // Si el modal de advertencia está visible, el usuario interactuó - cerrar modal y reiniciar
    if (showWarningModal.value) {
      cleanup();
    }
    
    // Limpiar timer anterior
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
    }
    
    // Solo iniciar timer si hay un usuario autenticado
    if (authStore.user && localStorage.getItem('userToken')) {
      inactivityTimer = setTimeout(() => {
        showWarning();
      }, INACTIVITY_TIMEOUT);
    }
  };

  /**
   * El usuario decidió continuar la sesión
   */
  const continueSession = () => {
    cleanup();
    resetInactivityTimer();
    notify.success('Sesión extendida', 'Tu sesión continúa activa.');
  };

  /**
   * El usuario decidió cerrar sesión manualmente desde el modal
   */
  const logoutNow = () => {
    logout();
  };

  /**
   * Configura los event listeners
   */
  const setupActivityListeners = () => {
    ACTIVITY_EVENTS.forEach(event => {
      document.addEventListener(event, resetInactivityTimer, { passive: true });
    });
  };

  /**
   * Remueve los event listeners
   */
  const removeActivityListeners = () => {
    ACTIVITY_EVENTS.forEach(event => {
      document.removeEventListener(event, resetInactivityTimer);
    });
  };

  /**
   * Inicia el sistema de detección de inactividad
   */
  const startInactivityDetection = () => {
    setupActivityListeners();
    resetInactivityTimer();
  };

  /**
   * Detiene el sistema de detección de inactividad
   */
  const stopInactivityDetection = () => {
    removeActivityListeners();
    cleanup();
  };

  onMounted(() => {
    startInactivityDetection();
  });

  onUnmounted(() => {
    stopInactivityDetection();
  });

  return {
    showWarningModal,
    secondsRemaining,
    continueSession,
    logoutNow,
    startInactivityDetection,
    stopInactivityDetection
  };
}
