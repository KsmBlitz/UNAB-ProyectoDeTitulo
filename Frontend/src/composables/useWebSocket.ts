// Frontend/src/composables/useWebSocket.ts
/**
 * Composable para WebSocket con reconexión automática
 * Reemplaza polling de alertas por comunicación en tiempo real
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { API_BASE_URL } from '@/config/api'

export interface WebSocketMessage {
  type: 'initial' | 'update' | 'dismissed' | 'heartbeat' | 'refresh' | 'error' | 'pong' | 'sensor_update'
  timestamp: string
  data?: any
  alert_id?: string
  message?: string
}

export interface WebSocketOptions {
  url: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const reconnectTimer = ref<number | null>(null)

  // Construir URL WebSocket (ws:// o wss://)
  const getWsUrl = (): string => {
    const baseUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    return `${baseUrl}${url}`
  }

  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected')
      return
    }

    try {
      const wsUrl = getWsUrl()
      console.log(`[WebSocket] Connecting to ${wsUrl}`)
      
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log('[WebSocket] Connected')
        isConnected.value = true
        reconnectAttempts.value = 0
        
        if (onConnect) {
          onConnect()
        }
      }

      ws.value.onmessage = (event: MessageEvent) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log('[WebSocket] Message received:', message.type)
          
          if (onMessage) {
            onMessage(message)
          }
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error)
        }
      }

      ws.value.onclose = (event: CloseEvent) => {
        console.log(`[WebSocket] Disconnected (code: ${event.code})`)
        isConnected.value = false
        ws.value = null
        
        if (onDisconnect) {
          onDisconnect()
        }

        // Intentar reconectar
        if (reconnectAttempts.value < maxReconnectAttempts) {
          scheduleReconnect()
        } else {
          console.error('[WebSocket] Max reconnect attempts reached')
        }
      }

      ws.value.onerror = (error: Event) => {
        console.error('[WebSocket] Error:', error)
        
        if (onError) {
          onError(error)
        }
      }
    } catch (error) {
      console.error('[WebSocket] Connection error:', error)
      scheduleReconnect()
    }
  }

  const scheduleReconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
    }

    reconnectAttempts.value++
    const delay = reconnectInterval * Math.min(reconnectAttempts.value, 5) // Backoff exponencial limitado

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.value}/${maxReconnectAttempts})`)
    
    reconnectTimer.value = window.setTimeout(() => {
      connect()
    }, delay)
  }

  const disconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }

    if (ws.value) {
      console.log('[WebSocket] Closing connection')
      ws.value.close(1000, 'Client disconnect')
      ws.value = null
    }

    isConnected.value = false
  }

  const send = (data: any) => {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] Cannot send, not connected')
      return false
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      ws.value.send(message)
      return true
    } catch (error) {
      console.error('[WebSocket] Send error:', error)
      return false
    }
  }

  const ping = () => {
    return send({ action: 'ping' })
  }

  const refresh = () => {
    return send({ action: 'refresh' })
  }

  // Auto-connect en mount
  onMounted(() => {
    connect()
  })

  // Cleanup en unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    reconnectAttempts,
    connect,
    disconnect,
    send,
    ping,
    refresh
  }
}


/**
 * Composable específico para alertas en tiempo real
 */
export function useAlertsWebSocket(onAlertUpdate: (data: any) => void) {
  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'initial':
      case 'update':
      case 'refresh':
        if (message.data) {
          onAlertUpdate(message.data)
        }
        break
      
      case 'dismissed':
        if (message.alert_id) {
          onAlertUpdate({ dismissed: message.alert_id })
        }
        break
      
      case 'heartbeat':
        // Silencioso, solo para keep-alive
        break
      
      case 'error':
        console.error('[Alerts WS] Server error:', message.message)
        break
    }
  }

  const handleConnect = () => {
    console.log('[Alerts WS] Connected to real-time alerts')
  }

  const handleDisconnect = () => {
    console.log('[Alerts WS] Disconnected from real-time alerts')
  }

  return useWebSocket({
    url: '/ws/alerts',
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10
  })
}


/**
 * Composable específico para datos de sensores en tiempo real
 */
export function useSensorsWebSocket(onSensorUpdate: (data: any) => void) {
  const handleMessage = (message: WebSocketMessage) => {
    if (message.type === 'sensor_update' && message.data) {
      onSensorUpdate(message.data)
    }
  }

  return useWebSocket({
    url: '/ws/sensors',
    onMessage: handleMessage,
    reconnectInterval: 5000,
    maxReconnectAttempts: 5
  })
}
