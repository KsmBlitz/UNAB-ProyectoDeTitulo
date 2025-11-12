# WebSocket Real-Time Communication

## Descripción

Sistema de comunicación bidireccional en tiempo real usando WebSockets. Elimina la necesidad de polling, reduciendo latencia y carga en el servidor.

## Arquitectura

```
┌─────────────┐        WebSocket         ┌──────────────┐
│   Frontend  │ ◄────────────────────► │   Backend    │
│  (Vue 3)    │   ws://localhost:8000   │  (FastAPI)   │
└─────────────┘                          └──────────────┘
       │                                        │
       │                                        │
       ▼                                        ▼
  useWebSocket()                         ConnectionManager
  composable                             + broadcast()
```

## Endpoints Disponibles

### 1. `/ws/alerts` - Alertas en Tiempo Real

**Propósito**: Notificaciones instantáneas de alertas sin polling

**Mensajes del Servidor → Cliente:**

```typescript
// Estado inicial al conectar
{
  "type": "initial",
  "timestamp": "2025-11-11T10:30:00Z",
  "data": {
    "total": 3,
    "critical": 1,
    "warning": 2,
    "info": 0
  }
}

// Nueva alerta detectada
{
  "type": "update",
  "timestamp": "2025-11-11T10:31:00Z",
  "data": {
    "total": 4,
    "critical": 2,
    "warning": 2,
    "info": 0
  }
}

// Alerta cerrada
{
  "type": "dismissed",
  "timestamp": "2025-11-11T10:32:00Z",
  "alert_id": "alerta_123"
}

// Keep-alive (cada 30s)
{
  "type": "heartbeat",
  "timestamp": "2025-11-11T10:33:00Z"
}
```

**Mensajes del Cliente → Servidor:**

```typescript
// Ping para verificar conexión
{
  "action": "ping"
}
// Respuesta: {"type": "pong", "timestamp": "..."}

// Solicitar actualización manual
{
  "action": "refresh"
}
// Respuesta: {"type": "refresh", "data": {...}}
```

### 2. `/ws/sensors` - Datos de Sensores

**Propósito**: Stream de datos de sensores cada 10 segundos

**Mensajes del Servidor:**

```typescript
{
  "type": "sensor_update",
  "timestamp": "2025-11-11T10:30:00Z",
  "data": {
    "temperature": 22.5,
    "ph": 5.3,
    "conductivity": 0.8,
    "water_level": 75.0,
    "reservoir_id": "EMBALSE_01"
  }
}
```

## Uso en Frontend

### Opción 1: Composable Genérico

```typescript
import { useWebSocket } from '@/composables/useWebSocket'

const handleMessage = (message: any) => {
  console.log('Mensaje recibido:', message)
}

const { isConnected, send, ping } = useWebSocket({
  url: '/ws/alerts',
  onMessage: handleMessage,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10
})

// Enviar mensaje
send({ action: 'ping' })
```

### Opción 2: Composable Específico para Alertas

```vue
<script setup lang="ts">
import { useAlertsWebSocket } from '@/composables/useWebSocket'
import { alertStore } from '@/stores/alertStore'

const handleAlertUpdate = (data: any) => {
  // Actualizar store con datos en tiempo real
  alertStore.summary = {
    total: data.total || 0,
    critical: data.critical || 0,
    warning: data.warning || 0,
    info: data.info || 0,
    has_critical: (data.critical || 0) > 0,
    last_updated: new Date().toISOString()
  }
}

const { isConnected, reconnectAttempts } = useAlertsWebSocket(handleAlertUpdate)
</script>

<template>
  <div>
    <span v-if="isConnected" class="text-green-500">
      <i class="pi pi-check-circle"></i> Conectado
    </span>
    <span v-else class="text-orange-500">
      <i class="pi pi-exclamation-triangle"></i>
      Reconectando... (intento {{ reconnectAttempts }})
    </span>
  </div>
</template>
```

## Características

### ✅ Reconexión Automática

```typescript
reconnectInterval: 3000,        // Espera 3s antes de reconectar
maxReconnectAttempts: 10        // Máximo 10 intentos
```

Backoff exponencial: 3s → 6s → 9s → 12s → 15s (máximo)

### ✅ Keep-Alive / Heartbeat

- Servidor envía `heartbeat` cada 30 segundos
- Previene desconexión por inactividad
- Cliente puede enviar `ping` manualmente

### ✅ Manejo de Errores

```typescript
onError: (error: Event) => {
  console.error('WebSocket error:', error)
  // Notificar al usuario
}
```

### ✅ Cleanup Automático

- Se desconecta automáticamente en `onUnmounted()`
- Limpia timers de reconexión
- No hay memory leaks

## Integración con Backend

### Broadcast a Todos los Clientes

```python
# En alert_watcher.py
from app.routes.websocket import broadcast_alert_update

async def notify_new_alert(alert_data: dict):
    # Enviar a todos los clientes conectados
    await broadcast_alert_update({
        "total": 5,
        "critical": 2,
        "warning": 3,
        "info": 0
    })
```

### Broadcast al Cerrar Alerta

```python
# En alerts.py
from app.routes.websocket import broadcast_alert_dismissed

@router.post("/alerts/dismiss")
async def dismiss_alert(request: DismissAlertRequest, ...):
    # ... cerrar alerta ...
    
    # Notificar a todos los clientes
    await broadcast_alert_dismissed(request.alert_id)
```

## Comparación: Polling vs WebSocket

### ❌ Polling (Anterior)

```typescript
// TheHeader.vue
setInterval(() => {
  alertStore.fetchSummary()  // Request cada 10 segundos
}, 10000)
```

**Problemas:**
- 360 requests/hora por usuario
- Latencia de hasta 10 segundos
- Desperdicio de ancho de banda (sin cambios)
- Carga innecesaria en el servidor

### ✅ WebSocket (Nuevo)

```typescript
// TheHeader.vue
const ws = useAlertsWebSocket(handleAlertUpdate)
```

**Ventajas:**
- 0 requests después de conectar
- Latencia < 100ms
- Solo envía cuando hay cambios
- 90% menos carga en servidor

## Monitoreo

### Ver Conexiones Activas

```python
# En websocket.py
from app.routes.websocket import manager

print(f"Conexiones activas: {len(manager.active_connections)}")
```

### Logs

```
[WebSocket] Connected. Total connections: 5
[WebSocket] Message received: ping
[WebSocket] Disconnected. Total connections: 4
```

## Testing

### Test Manual con wscat

```bash
# Instalar wscat
npm install -g wscat

# Conectar a alertas
wscat -c ws://localhost:8000/ws/alerts

# Enviar ping
> {"action": "ping"}
< {"type": "pong", "timestamp": "2025-11-11T10:30:00Z"}

# Solicitar refresh
> {"action": "refresh"}
< {"type": "refresh", "data": {...}}
```

### Test desde Browser DevTools

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts')

ws.onopen = () => console.log('Connected')
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data))
ws.send(JSON.stringify({ action: 'ping' }))
```

## Troubleshooting

### Problema: WebSocket no conecta

```
[WebSocket] Connection error: ...
```

**Solución:**
1. Verificar que el backend esté corriendo
2. Verificar CORS (debe permitir origen)
3. Verificar firewall (puerto 8000)

### Problema: Reconexiones constantes

```
[WebSocket] Reconnecting... (attempt 5/10)
```

**Causas comunes:**
- Backend reiniciando
- Proxy/Load balancer no soporta WebSocket
- Timeout del servidor muy corto

**Solución:**
- Aumentar `maxReconnectAttempts`
- Configurar proxy para WebSocket
- Ajustar timeout del servidor

## Roadmap

- [ ] Autenticación con JWT en WebSocket handshake
- [ ] Rooms/Channels para diferentes tipos de updates
- [ ] Compresión de mensajes (gzip/deflate)
- [ ] Métricas de latencia y throughput
- [ ] Fallback automático a polling si WebSocket falla
