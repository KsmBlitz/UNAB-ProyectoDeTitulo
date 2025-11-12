# Rate Limiting por Usuario y Rol

## 📋 Descripción

Sistema de **rate limiting inteligente** que aplica límites diferentes según el **rol del usuario** extraído del token JWT. Protege la API contra abuso y ataques DDoS mientras permite operaciones normales.

## 🎯 Límites por Rol

### Límites por Minuto (Ventana de 60 segundos)

| Rol | Límite | Uso Típico |
|-----|--------|------------|
| **Administrador** | ❌ Sin límite | Gestión completa del sistema |
| **Operario** | ✅ 300 req/min | Monitoreo intensivo, dashboards |
| **Usuario** | ✅ 200 req/min | Consultas normales, visualización |
| **Anónimo** (sin token) | ⚠️ 100 req/min | Acceso público limitado |

### Límites por Hora (Solo usuarios autenticados)

- **Usuarios autenticados**: 10,000 requests/hora
- **Administradores**: Sin límite horario

### Límites para Endpoints Críticos

**Aplica a TODOS los roles** (incluidos administradores):

- **5 requests/minuto** para:
  - `/api/token` (Login)
  - `/api/forgot-password`
  - `/api/reset-password`
  - `POST /api/users` (Crear usuario)

## 🔧 Implementación Técnica

### Extracción del Rol del Token JWT

```python
# El middleware decodifica el token y extrae:
{
  "sub": "usuario@example.com",  # Email (identificador único)
  "role": "operario",             # Rol del usuario
  "exp": 1234567890               # Expiración
}
```

### Tracking de Requests

**Por IP (ventana de 1 minuto)**:
```python
ip_requests = {
    "192.168.1.100": [
        (timestamp, "/api/sensors"),
        (timestamp, "/api/alerts"),
        ...
    ]
}
```

**Por Usuario (ventana de 1 hora)**:
```python
user_requests = {
    "operario@example.com": [
        (timestamp, "/api/sensors", "operario"),
        (timestamp, "/api/alerts", "operario"),
        ...
    ]
}
```

## 📊 Headers de Respuesta

Todas las respuestas incluyen headers informativos:

```http
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 287
X-RateLimit-Reset: 1234567890
X-RateLimit-Role: operario
```

### Para Administradores

```http
X-RateLimit-Limit: unlimited
X-RateLimit-Remaining: unlimited
X-RateLimit-Role: administrador
```

## ⚠️ Respuestas de Rate Limit Excedido

### HTTP 429 - Too Many Requests

```json
{
  "detail": "Límite de solicitudes excedido (300/min). Intenta nuevamente en 1 minuto.",
  "retry_after": 60,
  "limit": 300,
  "role": "operario"
}
```

Headers de respuesta:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json
```

### Endpoint Crítico Excedido

```json
{
  "detail": "Demasiadas solicitudes. Por favor, espera 1 minuto antes de intentar nuevamente.",
  "retry_after": 60
}
```

## 🚀 Uso en el Frontend

### Manejo de Rate Limiting

```typescript
// Frontend/src/composables/useApi.ts
import { ref } from 'vue';

export function useApiWithRateLimit() {
  const rateLimitInfo = ref({
    limit: 0,
    remaining: 0,
    reset: 0,
    role: ''
  });

  async function fetchWithRateLimitTracking(url: string, options?: RequestInit) {
    try {
      const response = await fetch(url, options);
      
      // Extraer headers de rate limit
      rateLimitInfo.value = {
        limit: parseInt(response.headers.get('X-RateLimit-Limit') || '0'),
        remaining: parseInt(response.headers.get('X-RateLimit-Remaining') || '0'),
        reset: parseInt(response.headers.get('X-RateLimit-Reset') || '0'),
        role: response.headers.get('X-RateLimit-Role') || ''
      };

      if (response.status === 429) {
        const data = await response.json();
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        
        throw new Error(`Rate limit excedido. Reintenta en ${retryAfter} segundos.`);
      }

      return response;
    } catch (error) {
      console.error('Error en request:', error);
      throw error;
    }
  }

  return { fetchWithRateLimitTracking, rateLimitInfo };
}
```

### Componente de Advertencia

```vue
<template>
  <div v-if="rateLimitInfo.remaining < 20" class="rate-limit-warning">
    <p>
      ⚠️ Quedan {{ rateLimitInfo.remaining }} de {{ rateLimitInfo.limit }} requests disponibles
    </p>
    <p v-if="rateLimitInfo.remaining === 0">
      Rate limit alcanzado. Se reiniciará en {{ timeUntilReset }} segundos.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useApiWithRateLimit } from '@/composables/useApi';

const { rateLimitInfo } = useApiWithRateLimit();

const timeUntilReset = computed(() => {
  const now = Math.floor(Date.now() / 1000);
  return Math.max(0, rateLimitInfo.value.reset - now);
});
</script>
```

## 🔍 Monitoreo y Estadísticas

### Endpoint de Estadísticas (Solo Administradores)

```bash
GET /api/rate-limit/stats
Authorization: Bearer <admin_token>
```

**Respuesta:**
```json
{
  "active_ips": 45,
  "active_users": 23,
  "total_ip_requests": 1234,
  "total_user_requests": 5678,
  "requests_by_role": {
    "administrador": 234,
    "operario": 2890,
    "usuario": 1554,
    "anonymous": 1000
  },
  "rate_limits": {
    "administrador": "unlimited",
    "operario": "300/min",
    "usuario": "200/min",
    "anonymous": "100/min",
    "critical_endpoints": "5/min",
    "hourly_limit": "10000/hour"
  }
}
```

## 🧪 Testing

### Test 1: Usuario Normal

```bash
# Login como usuario normal
TOKEN=$(curl -X POST http://localhost:8000/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=usuario@example.com&password=password" \
  | jq -r '.access_token')

# Hacer 210 requests (excede límite de 200/min)
for i in {1..210}; do
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/sensors \
    -w "\nStatus: %{http_code}, Request: $i\n"
done

# Resultado esperado: 
# - Requests 1-200: HTTP 200
# - Requests 201-210: HTTP 429
```

### Test 2: Operario

```bash
# Login como operario
TOKEN=$(curl -X POST http://localhost:8000/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=operario@example.com&password=password" \
  | jq -r '.access_token')

# Hacer 310 requests (excede límite de 300/min)
for i in {1..310}; do
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/sensors \
    -w "\nStatus: %{http_code}, Remaining: %header{X-RateLimit-Remaining}\n"
done

# Resultado esperado:
# - Requests 1-300: HTTP 200
# - Requests 301-310: HTTP 429
```

### Test 3: Administrador (Sin límite)

```bash
# Login como administrador
TOKEN=$(curl -X POST http://localhost:8000/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123" \
  | jq -r '.access_token')

# Hacer 500 requests (no debe haber límite)
for i in {1..500}; do
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/sensors \
    -w "\nStatus: %{http_code}, Limit: %header{X-RateLimit-Limit}\n"
done

# Resultado esperado:
# - Todos los requests: HTTP 200
# - Header: X-RateLimit-Limit: unlimited
```

### Test 4: Endpoint Crítico

```bash
# Intentar login 6 veces en 1 minuto (límite: 5)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@example.com&password=wrong" \
    -w "\nStatus: %{http_code}, Attempt: $i\n"
  sleep 1
done

# Resultado esperado:
# - Intentos 1-5: HTTP 401 (credenciales inválidas)
# - Intento 6: HTTP 429 (rate limit excedido)
```

### Test 5: Usuario Anónimo

```bash
# Requests sin token (máximo 100/min)
for i in {1..105}; do
  curl http://localhost:8000/api/sensors/public \
    -w "\nStatus: %{http_code}, Request: $i\n"
done

# Resultado esperado:
# - Requests 1-100: HTTP 200
# - Requests 101-105: HTTP 429
```

## 📈 Beneficios

### Seguridad

- ✅ **Protección contra brute force** en login/reset password (5 intentos/min)
- ✅ **Prevención de DDoS** por usuario o IP
- ✅ **Rate limiting diferenciado** por rol (operarios necesitan más límite)

### Rendimiento

- ✅ **Limpieza automática** de requests antiguos (ventana deslizante)
- ✅ **Sin base de datos** (estado en memoria del middleware)
- ✅ **O(1) tracking** por IP y usuario

### Monitoreo

- ✅ **Headers informativos** en cada response
- ✅ **Endpoint de estadísticas** para administradores
- ✅ **Logging estructurado** de violaciones

## 🛠️ Configuración Avanzada

### Ajustar Límites

Editar `Backend/app/middleware/rate_limit.py`:

```python
self.ROLE_LIMITS = {
    "administrador": None,  # Sin límite
    "operario": 500,        # Aumentar a 500/min
    "usuario": 200,
    "anonymous": 50         # Reducir a 50/min
}

self.USER_LIMIT_PER_HOUR = 20000  # Aumentar límite horario
self.CRITICAL_ENDPOINTS_LIMIT = 3  # Reducir a 3 intentos/min
```

### Excluir Rutas

```python
async def dispatch(self, request: Request, call_next):
    # Excluir rutas específicas
    if (request.url.path.startswith("/health") or 
        request.url.path == "/" or 
        request.url.path.startswith("/ws/") or
        request.url.path.startswith("/docs")):  # Agregar /docs
        return await call_next(request)
```

### Agregar Endpoint Crítico

```python
self.CRITICAL_ENDPOINTS = [
    "/api/token",
    "/api/forgot-password",
    "/api/reset-password",
    "/api/users",
    "/api/admin/delete-all"  # Nuevo endpoint crítico
]
```

## 🐛 Troubleshooting

### Problema: Rate limit se aplica incorrectamente

**Síntoma**: Usuario con rol `operario` recibe límite de 200/min en lugar de 300/min.

**Solución**: Verificar que el token incluya el campo `role`:

```bash
# Decodificar token JWT
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq

# Debe mostrar:
{
  "sub": "operario@example.com",
  "role": "operario",  # ← Verificar que exista
  "exp": 1234567890
}
```

### Problema: Administrador recibe HTTP 429

**Síntoma**: Administrador es bloqueado por rate limiting.

**Causa**: Endpoints críticos aplican a todos los roles.

**Solución**: Los administradores están exentos del rate limit general, pero NO de los endpoints críticos (login, reset password). Esto es intencional por seguridad.

### Problema: Rate limit no se reinicia

**Síntoma**: Usuario sigue bloqueado después de 1 minuto.

**Causa**: El middleware limpia automáticamente requests antiguos, pero el usuario debe esperar que la ventana se deslice.

**Solución**: Esperar 60 segundos completos desde el último request bloqueado.

## 📚 Referencias

- [RFC 6585 - HTTP 429](https://tools.ietf.org/html/rfc6585#section-4)
- [OWASP Rate Limiting](https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

## 🔗 Archivos Relacionados

- `Backend/app/middleware/rate_limit.py` - Implementación del middleware
- `Backend/main.py` - Integración y endpoint de estadísticas
- `Backend/app/services/auth.py` - Generación de tokens con rol

---

**Implementado en**: Commit 8  
**Autor**: Sistema de Monitoreo IoT  
**Fecha**: 2024
