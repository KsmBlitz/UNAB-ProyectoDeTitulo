// Frontend/src/stores/alertStoreWebSocket.ts
/**
 * Ejemplo de integración de WebSocket en alertStore
 * Reemplaza polling por actualizaciones en tiempo real
 */

import { useAlertsWebSocket } from '@/composables/useWebSocket'

// En el componente TheHeader.vue o donde se use el store:

/*
<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { alertStore } from '@/stores/alertStore'
import { useAlertsWebSocket } from '@/composables/useWebSocket'

// Callback cuando llegan actualizaciones de alertas
const handleAlertUpdate = (data: any) => {
  if (data.dismissed) {
    // Una alerta fue cerrada
    alertStore.removeAlert(data.dismissed)
    alertStore.fetchSummary() // Actualizar resumen
  } else {
    // Nueva alerta o actualización
    alertStore.summary = {
      total: data.total || 0,
      critical: data.critical || 0,
      warning: data.warning || 0,
      info: data.info || 0,
      has_critical: (data.critical || 0) > 0,
      last_updated: new Date().toISOString()
    }
    
    // Opcionalmente recargar alertas completas
    alertStore.fetchActiveAlerts()
  }
}

// Conectar WebSocket
const { isConnected, reconnectAttempts } = useAlertsWebSocket(handleAlertUpdate)

onMounted(() => {
  // Ya no necesitamos polling
  // alertStore.startPolling() ← ELIMINAR ESTO
  
  // Cargar datos iniciales
  alertStore.fetchSummary()
  alertStore.fetchActiveAlerts()
})

onUnmounted(() => {
  // WebSocket se desconecta automáticamente
  // alertStore.stopPolling() ← YA NO NECESARIO
})
</script>
*/

// Método helper para agregar al store
export function initializeWebSocketAlerts(store: any) {
  const handleAlertUpdate = (data: any) => {
    if (data.dismissed) {
      // Remover alerta del array
      const index = store.activeAlerts.findIndex((a: any) => a.id === data.dismissed)
      if (index !== -1) {
        store.activeAlerts.splice(index, 1)
      }
      store.fetchSummary()
    } else {
      // Actualizar resumen
      store.summary = {
        total: data.total || 0,
        critical: data.critical || 0,
        warning: data.warning || 0,
        info: data.info || 0,
        has_critical: (data.critical || 0) > 0,
        last_updated: new Date().toISOString()
      }
    }
  }

  return useAlertsWebSocket(handleAlertUpdate)
}


/**
 * MIGRACIÓN: Pasos para reemplazar polling por WebSocket
 * 
 * 1. En TheHeader.vue o componente principal:
 *    - Importar: import { initializeWebSocketAlerts } from '@/stores/alertStoreWebSocket'
 *    - En setup(): const ws = initializeWebSocketAlerts(alertStore)
 *    - Eliminar: alertStore.startPolling() y alertStore.stopPolling()
 * 
 * 2. Opcional - Mostrar indicador de conexión:
 *    <div v-if="!ws.isConnected" class="text-orange-500">
 *      <i class="pi pi-exclamation-triangle"></i>
 *      Reconectando... ({{ ws.reconnectAttempts }})
 *    </div>
 * 
 * 3. En alerts.py backend, cuando se dismissea una alerta:
 *    from app.routes.websocket import broadcast_alert_dismissed
 *    await broadcast_alert_dismissed(alert_id)
 * 
 * 4. En alert_watcher.py, cuando se detecta nueva alerta:
 *    from app.routes.websocket import broadcast_alert_update
 *    await broadcast_alert_update(alert_data)
 */
