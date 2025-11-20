# Sistema IoT Monitoreo de Embalses para Arándanos# Sistema IoT de Monitoreo de Calidad del Agua para Cultivos de Arándanos



Sistema de monitoreo en tiempo real de la calidad del agua en embalses para cultivos de arándanos utilizando IoT, desarrollado con FastAPI, MongoDB, Redis y Vue.js.![Vue.js](https://img.shields.io/badge/Vue.js-3.5-4FC08D?logo=vue.js&logoColor=white)

![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript&logoColor=white)

## Inicio Rápido![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)

### Requisitos Previos![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)

- Docker y Docker Compose![AWS IoT](https://img.shields.io/badge/AWS_IoT-FF9900?logo=amazonaws&logoColor=white)

- Node.js 20+ (solo para desarrollo frontend)![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?logo=docker&logoColor=white)

- Python 3.11+ (solo para desarrollo backend)![ML](https://img.shields.io/badge/ML-Scikit--learn-F7931E?logo=scikit-learn&logoColor=white)

![Status](https://img.shields.io/badge/Status-Producci%C3%B3n-success)

### Instalación

## Descripción

1. **Clonar el repositorio**

```bashPlataforma IoT empresarial completa para el monitoreo inteligente de calidad del agua en cultivos de arándanos en Chile. Integra sensores en tiempo real con AWS IoT Core, predicción mediante Machine Learning, sistema de alertas multinivel, y auditoría completa de eventos del sistema.

git clone https://github.com/KsmBlitz/UNAB-ProyectoDeTitulo.git

cd UNAB-ProyectoDeTitulo**Especializado para arándanos chilenos:** pH óptimo 5.0-5.5, conductividad eléctrica <1.5 dS/m.

```

### Objetivos Principales

2. **Configurar variables de entorno**- Monitoreo en tiempo real de pH, conductividad eléctrica, temperatura y nivel de agua

```bash- Predicción inteligente con Machine Learning (regresión lineal) de valores futuros

# Backend- Sistema de alertas proactivo con notificaciones automáticas (Email/WhatsApp)

cp Backend/.env.example Backend/.env- Gestión de usuarios con roles (Admin/Operario) y autenticación JWT

# Editar Backend/.env con tus credenciales- Auditoría completa de todas las acciones críticas del sistema

- Visualización avanzada con gráficos históricos y tendencias predictivas

# Frontend

cp Frontend/.env.example Frontend/.env---

```

## Características Implementadas

3. **Levantar servicios con Docker Compose**

```bash### Autenticación y Seguridad

docker-compose up -d- Login/Logout JWT con tokens seguros y renovación automática

```- Recuperación de contraseña vía SMTP (Gmail/personalizado)

- Sistema de roles RBAC: Administrador y Operario con permisos granulares

4. **Acceder a la aplicación**- Hash bcrypt para contraseñas con salt rounds configurables

- Frontend: http://localhost- Protección de rutas en frontend y backend con middleware

- Backend API: http://localhost/api- Validación de tokens y manejo de expiración automático

- Documentación API: http://localhost/api/docs

### Dashboard en Tiempo Real

### Usuario por Defecto- Métricas actualizadas cada 30 segundos automáticamente

- Email: admin@example.com- Cards responsivos con indicadores de estado por colores (verde/amarillo/rojo)

- Password: admin123- Gráficos históricos interactivos con Chart.js y zoom

- Gráficos individuales para cada métrica (pH, EC, Temperatura)

## Arquitectura- Selector de rangos: Últimas 24h, 7 días, 30 días, rango personalizado

- Modo claro/oscuro persistente con transiciones suaves

El sistema sigue una arquitectura de microservicios con los siguientes componentes:- Diseño responsive optimizado para desktop, tablet y móvil



- **Backend**: FastAPI + Motor (MongoDB async) + Redis### Predicción con Machine Learning

- **Frontend**: Vue 3 + TypeScript + Tailwind CSS- Modelo de regresión lineal entrenado con datos históricos

- **Base de Datos**: MongoDB- Predicción de pH y Conductividad para los próximos N días (configurable)

- **Cache**: Redis- Configuración dinámica: Días a predecir (1-30) y días históricos (1-90)

- **Proxy**: Nginx- Visualización integrada de predicciones en gráficos con línea punteada

- Detección de valores críticos en predicciones futuras

### Estructura del Proyecto- Alertas predictivas cuando se prevén valores fuera de rango

```- Modal de configuración con validación en tiempo real

UNAB-ProyectoDeTitulo/- Registro en auditoría de cambios en parámetros del modelo

├── Backend/              # API REST con FastAPI

│   ├── app/### Sistema de Alertas Multinivel

│   │   ├── models/       # Modelos de datos- Detección automática cada 6 minutos mediante servicio de fondo

│   │   ├── routes/       # Endpoints de la API- Tres niveles de severidad: Info (azul), Warning (amarillo), Critical (rojo)

│   │   ├── services/     # Lógica de negocio- Umbrales personalizables por métrica y nivel

│   │   ├── repositories/ # Capa de acceso a datos- Notificaciones automáticas:

│   │   ├── middleware/   # Middlewares (rate limit, CORS, etc.)  - Email SMTP con plantillas HTML profesionales

│   │   └── utils/        # Utilidades  - WhatsApp Business API (preparado para integración)

│   ├── tests/            # Tests unitarios- Período de gracia: 1 hora para evitar alertas duplicadas

│   └── Dockerfile- Dismissal manual con registro de quién cerró cada alerta

├── Frontend/             # Dashboard Vue.js- Historial completo con filtros por severidad, métrica y fecha

│   ├── src/- Estados: Activa, Resuelta, Auto-resuelta

│   │   ├── components/   # Componentes reutilizables- Duración calculada automáticamente al resolver

│   │   ├── views/        # Vistas/páginas

│   │   ├── stores/       # Gestión de estado### Auditoría y Trazabilidad

│   │   └── router/       # Rutas- Registro automático de todas las acciones críticas del sistema

│   └── Dockerfile- Eventos auditados:

├── docs/                 # Documentación completa  - Login/Logout de usuarios

└── docker-compose.yml    # Orquestación de servicios  - Creación/Edición/Eliminación de usuarios

```  - Cambios en configuración de alertas

  - Dismissal de alertas con usuario responsable

## Documentación  - Actualización de parámetros del modelo ML

- Metadata completa: Usuario, timestamp, IP, detalles de la acción

Toda la documentación técnica se encuentra en la carpeta `/docs`:- Filtros avanzados: Por acción, usuario, rango de fechas

- Interfaz visual con badges de colores por tipo de evento

### Arquitectura y Diseño- Exportable para auditorías externas (preparado)

- [Arquitectura de Microservicios](docs/ARQUITECTURA-MICROSERVICIOS.md)

- [Principios SOLID](docs/PRINCIPIOS-SOLID.md)### Gestión de Usuarios (Solo Administradores)

- [Auditoría de Arquitectura](docs/AUDITORIA-ARQUITECTURA.md)- CRUD completo con interfaz moderna

- Validación robusta: Emails únicos, campos requeridos, formato correcto

### Funcionalidades- Asignación de roles con permisos diferenciados

- [Autenticación y Autorización](docs/AUTENTICACION-DOCS.md)- Deshabilitación de usuarios sin eliminación permanente

- [Rate Limiting](docs/RATE-LIMITING.md)- Tabla interactiva con búsqueda y paginación

- [WebSocket](docs/WEBSOCKET.md)- Modales de creación/edición con feedback visual

- [PWA](docs/PWA.md)- Confirmación de acciones críticas (eliminar usuario)



### Testing y Operaciones### Conectividad IoT

- [Guía de Testing](docs/TESTING.md)- AWS IoT Core configurado con certificados TLS

- [Cambiar Credenciales](docs/CAMBIAR-CREDENCIALES.md)- Comunicación MQTT segura para sensores ESP32

- [Nuevas Características v2.0](docs/NUEVAS-CARACTERISTICAS-v2.0.md)- Ingesta de datos con validación de esquema

- Almacenamiento optimizado en MongoDB con índices

## Comandos Útiles- APIs REST documentadas con Swagger/ReDoc

- WebSockets preparados para streaming en tiempo real

### Docker

```bash### Experiencia de Usuario

# Iniciar servicios- Interfaz limpia con Tailwind CSS y componentes reutilizables

docker-compose up -d- Animaciones suaves en transiciones y modales

- Iconos profesionales con PrimeIcons

# Ver logs- Feedback visual inmediato en todas las acciones

docker-compose logs -f- Mensajes de error descriptivos y accionables

- Loading states para operaciones asíncronas

# Reiniciar un servicio- Toast notifications para eventos importantes

docker-compose restart backend- Sidebar colapsable con navegación intuitiva



# Rebuild sin caché---

docker-compose build --no-cache

## Arquitectura del Sistema

# Detener servicios

docker-compose down```mermaid

```graph TB

    subgraph "IoT Layer"

### Backend (Desarrollo)        ESP32[ESP32 + Sensores pH/EC/Temp]

```bash        AWS[AWS IoT Core<br/>MQTT + TLS]

cd Backend    end

    

# Instalar dependencias    subgraph "Backend Services"

pip install -r requirements.txt        API[FastAPI REST API<br/>Puerto 8000]

        ML[Servicio ML<br/>Scikit-learn]

# Ejecutar tests        ALERT[Alert Watcher<br/>Background Task]

pytest        AUDIT[Audit Service<br/>Logging]

        DB[(MongoDB<br/>Motor Async)]

# Ejecutar tests con cobertura    end

pytest --cov=app tests/    

    subgraph "External Services"

# Ejecutar localmente        SMTP[Gmail SMTP<br/>Notificaciones Email]

uvicorn main:app --reload --host 0.0.0.0 --port 8000        WA[WhatsApp Business API<br/>Mensajes]

```    end

    

### Frontend (Desarrollo)    subgraph "Frontend Application"

```bash        WEB[Vue 3 + TypeScript<br/>Puerto 3000]

cd Frontend        CHARTS[Chart.js<br/>Visualización]

        AUTH[JWT Auth<br/>Store]

# Instalar dependencias    end

npm install    

    ESP32 -->|MQTT Pub| AWS

# Desarrollo    AWS -->|HTTP Webhook| API

npm run dev    API <-->|CRUD Async| DB

    API --> ML

# Build producción    API --> ALERT

npm run build    API --> AUDIT

    ALERT -->|Email| SMTP

# Tests    ALERT -->|WhatsApp| WA

npm run test    WEB <-->|REST API| API

```    WEB --> CHARTS

    WEB --> AUTH

## Características Principales    

    style ESP32 fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#fff

- Monitoreo en tiempo real de sensores IoT (pH, conductividad, temperatura, nivel de agua)    style AWS fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#fff

- Sistema de alertas configurables con notificaciones (Email, WhatsApp)    style API fill:#4CAF50,stroke:#388E3C,stroke-width:2px,color:#fff

- Dashboard interactivo con gráficos históricos    style ML fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#fff

- Gestión de usuarios y roles (admin, operario)    style DB fill:#E91E63,stroke:#C2185B,stroke-width:2px,color:#fff

- Auditoría completa de acciones    style SMTP fill:#F44336,stroke:#D32F2F,stroke-width:2px,color:#fff

- Rate limiting y protección contra abusos    style WEB fill:#00BCD4,stroke:#0097A7,stroke-width:2px,color:#fff

- Cache con Redis para optimización```

- Health checks para monitoreo

- API RESTful documentada con OpenAPI/Swagger### Flujo de Datos



## Tecnologías Utilizadas1. **Sensores → Cloud:** ESP32 publica datos cada 5 minutos vía MQTT a AWS IoT Core

2. **Cloud → Backend:** AWS envía datos al endpoint FastAPI mediante HTTP

### Backend3. **Procesamiento:** FastAPI valida, procesa y almacena en MongoDB

- FastAPI 0.104.14. **Monitoreo:** Alert Watcher analiza valores cada 6 minutos

- Motor 3.3.2 (MongoDB async)5. **Notificaciones:** Si hay valores críticos, envía emails/WhatsApp automáticamente

- Redis 7.0.16. **Predicción:** Modelo ML se entrena con datos históricos bajo demanda

- Pydantic 2.5.07. **Visualización:** Frontend consulta APIs REST y actualiza gráficos cada 30s

- JWT para autenticación8. **Auditoría:** Todas las acciones críticas se registran automáticamente

- Pytest para testing

---

### Frontend

- Vue 3 con Composition API## Stack Tecnológico

- TypeScript

- Tailwind CSS| Categoría | Tecnologías |

- Chart.js para gráficos|-----------|------------|

- Vite como build tool| **Frontend** | Vue 3 (Composition API), TypeScript, Vite, Tailwind CSS |

| **Gráficos** | Chart.js, vue-chartjs |

### Infraestructura| **Backend** | Python 3.11, FastAPI, Pydantic v2, Uvicorn |

- Docker & Docker Compose| **Base de Datos** | MongoDB 7.0, Motor (async driver) |

- Nginx como reverse proxy| **ML/Predicción** | Scikit-learn, NumPy, Regresión Lineal |

- MongoDB para persistencia| **Autenticación** | JWT (python-jose), bcrypt, OAuth2 |

- Redis para cache| **IoT** | AWS IoT Core, MQTT, TLS/SSL Certificates |

| **Notificaciones** | Gmail SMTP, WhatsApp Business API |

## Contribuir| **DevOps** | Docker, Docker Compose, Nginx |

| **Testing** | Pytest, Pytest-asyncio, Vitest (frontend) |

1. Fork el proyecto| **Code Quality** | ESLint, Prettier, Black (Python) |

2. Crea tu Feature Branch (`git checkout -b feature/AmazingFeature`)| **Iconografía** | PrimeIcons, Lucide Icons |

3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)

4. Push a la Branch (`git push origin feature/AmazingFeature`)---

5. Abre un Pull Request

## Estructura del Proyecto

## Licencia

```

Este proyecto es parte de un proyecto de título académico de la Universidad Nacional Andrés Bello (UNAB).UNAB-ProyectoDeTitulo/

├── Backend/                          # API FastAPI + Servicios

## Contacto│   ├── main.py                      # Punto de entrada (deprecated, ver app/)

│   ├── requirements.txt             # Dependencias Python

Vicente Estay Valdivia - [@KsmBlitz](https://github.com/KsmBlitz)│   ├── pytest.ini                   # Configuración de tests

│   ├── Dockerfile                   # Imagen Docker del backend

Proyecto Link: [https://github.com/KsmBlitz/UNAB-ProyectoDeTitulo](https://github.com/KsmBlitz/UNAB-ProyectoDeTitulo)│   │

│   ├── app/                         # Aplicación modular FastAPI
│   │   ├── __init__.py
│   │   ├── config/                  # Configuración centralizada
│   │   │   ├── database.py          # Conexión MongoDB
│   │   │   └── settings.py          # Variables de entorno
│   │   │
│   │   ├── models/                  # Modelos de datos Pydantic
│   │   │   └── user.py              # Usuario con roles
│   │   │
│   │   ├── routes/                  # Endpoints REST API
│   │   │   ├── auth.py              # Login, logout, reset password
│   │   │   ├── users.py             # CRUD de usuarios
│   │   │   ├── sensors.py           # Datos de sensores + predicción
│   │   │   ├── alerts.py            # Gestión de alertas
│   │   │   └── audit.py             # Historial de auditoría
│   │   │
│   │   ├── services/                # Lógica de negocio
│   │   │   ├── auth.py              # Autenticación JWT
│   │   │   ├── email.py             # Envío de emails SMTP
│   │   │   ├── whatsapp.py          # Integración WhatsApp
│   │   │   ├── prediction.py        # Modelo ML (regresión)
│   │   │   ├── alert_watcher.py     # Servicio de alertas background
│   │   │   ├── audit.py             # Sistema de auditoría
│   │   │   └── notifications.py     # Notificaciones unificadas
│   │   │
│   │   └── utils/                   # Utilidades compartidas
│   │       └── dependencies.py      # Dependencias de FastAPI
│   │
│   ├── models/                      # Modelos de dominio
│   │   ├── alert_models.py          # Alertas y umbrales
│   │   └── audit_models.py          # Acciones de auditoría
│   │
│   ├── certificates/                # Certificados AWS IoT
│   │   ├── root-CA.pem
│   │   ├── device.pem.key.crt
│   │   └── private.pem.key
│   │
│   └── tests/                       # Tests unitarios y E2E
│       ├── conftest.py              # Fixtures compartidos
│       ├── test_auth.py
│       ├── test_notifications.py
│       └── test_routes.py
│
├── Frontend/                        # Aplicación Vue 3
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts               # Configuración Vite
│   ├── tsconfig.json                # TypeScript config
│   ├── tailwind.config.js           # Tailwind CSS
│   ├── nginx.conf                   # Nginx para producción
│   ├── Dockerfile                   # Imagen Docker del frontend
│   │
│   └── src/
│       ├── main.ts                  # Punto de entrada
│       ├── App.vue                  # Componente raíz
│       │
│       ├── views/                   # Páginas principales
│       │   ├── LoginView.vue
│       │   ├── ForgotPasswordView.vue
│       │   ├── ResetPasswordView.vue
│       │   ├── DashboardLayout.vue
│       │   ├── DashboardHomeView.vue
│       │   ├── UserManagementView.vue
│       │   ├── AlertsManagementView.vue
│       │   └── AuditLogView.vue
│       │
│       ├── components/              # Componentes reutilizables
│       │   ├── Sidebar.vue
│       │   ├── TheHeader.vue
│       │   ├── ThemeToggle.vue
│       │   ├── MetricCard.vue
│       │   ├── IndividualChart.vue  # Gráfico con predicción ML
│       │   ├── HistoricalChartGrid.vue
│       │   ├── SensorsTable.vue
│       │   ├── UsersTable.vue
│       │   ├── CreateUserModal.vue
│       │   └── EditUserModal.vue
│       │
│       ├── router/                  # Vue Router
│       │   └── index.ts             # Rutas y guards
│       │
│       ├── stores/                  # Pinia stores
│       │   ├── themeStore.ts
│       │   └── alertStore.ts
│       │
│       ├── auth/                    # Autenticación
│       │   └── store.ts             # Store de usuario
│       │
│       ├── composables/             # Lógica reutilizable
│       │   ├── useApi.ts
│       │   └── useClickOutside.ts
│       │
│       ├── config/                  # Configuración
│       │   └── api.ts               # Base URL API
│       │
│       ├── types/                   # Tipos TypeScript
│       │   └── index.ts
│       │
│       ├── utils/                   # Utilidades
│       │   ├── constants.ts
│       │   ├── helpers.ts
│       │   └── metrics.ts
│       │
│       └── assets/                  # Recursos estáticos
│           └── styles.css           # Estilos globales
│
├── docker-compose.yml               # Orquestación de servicios
└── README.md                        # Este archivo
```

---

## Instalación y Despliegue

### Prerrequisitos
- Docker 24.0+ y Docker Compose 2.0+
- Git para clonar el repositorio
- Cuenta Gmail o servidor SMTP para emails
- (Opcional) AWS IoT Core configurado con certificados

---

### 1. Clonar el Repositorio

```bash
git clone https://github.com/KsmBlitz/UNAB-ProyectoDeTitulo.git
cd UNAB-ProyectoDeTitulo
```

---

### 2. Configurar Variables de Entorno

Crear archivo `.env` en la carpeta `Backend/`:

```env
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
DATABASE_NAME=embalses_iot

# JWT Security
JWT_SECRET_KEY=tu_clave_super_secreta_aqui_cambiala_en_produccion_min_32_chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# SMTP Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password_de_gmail
SMTP_FROM_EMAIL=tu_email@gmail.com
SMTP_FROM_NAME=Sistema IoT Arándanos

# WhatsApp Business API (opcional)
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_ACCESS_TOKEN=tu_token_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_id

# AWS IoT Core (opcional, para sensores reales)
AWS_IOT_ENDPOINT=xxxxx.iot.us-east-1.amazonaws.com
AWS_REGION=us-east-1

# Application Settings
ALERT_CHECK_INTERVAL=360  # Segundos entre chequeos (6 min)
ALERT_GRACE_PERIOD=3600   # Período de gracia (1 hora)
```

Nota sobre Gmail: Debes activar "Verificación en 2 pasos" en tu cuenta Gmail, generar una "Contraseña de aplicación" específica. Instrucciones: https://support.google.com/accounts/answer/185833

---

### 3. Despliegue con Docker

Opción A: Despliegue Completo (Recomendado)

```bash
# Construir y levantar todos los servicios
docker-compose up -d --build

# Ver logs en tiempo real
docker-compose logs -f

# Verificar que los contenedores estén corriendo
docker ps
```

Opción B: Desarrollo Local (Sin Docker)

Backend:
```bash
cd Backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend:
```bash
cd Frontend
npm install
npm run dev  # Modo desarrollo (puerto 5173)
# O para producción:
npm run build
npm run preview
```

---

### 4. Acceso al Sistema

Una vez desplegado, accede a:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | Dashboard principal |
| Backend API | http://localhost:8000 | API REST |
| Documentación Swagger | http://localhost:8000/docs | API interactiva |
| ReDoc | http://localhost:8000/redoc | Documentación alternativa |
| MongoDB | localhost:27017 | Base de datos |

---

### 5. Crear Usuario Administrador

El sistema crea automáticamente un usuario admin al iniciar. Si necesitas crear uno manualmente:

Opción A: Usando la API (recomendado)

```bash
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@embalses.cl",
    "password": "Admin123!",
    "full_name": "Administrador Principal",
    "role": "admin"
  }'
```

Opción B: Desde el contenedor

```bash
docker exec -it embalses-backend python -c "
from app.config.database import get_database
from passlib.context import CryptContext
import asyncio

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def create_admin():
    db = await get_database()
    users = db.users
    
    # Verificar si ya existe
    existing = await users.find_one({'email': 'admin@embalses.cl'})
    if existing:
        print('Admin ya existe')
        return
    
    # Crear admin
    await users.insert_one({
        'email': 'admin@embalses.cl',
        'hashed_password': pwd_context.hash('Admin123!'),
        'full_name': 'Administrador',
        'role': 'admin',
        'disabled': False
    })
    print('Admin creado exitosamente')

asyncio.run(create_admin())
"
```

Credenciales por defecto:
- Email: `admin@embalses.cl`
- Contraseña: `Admin123!`
- Advertencia: Cámbialas inmediatamente en producción

---

### 6. Optimización de Base de Datos (Recomendado)

Para mejorar significativamente el rendimiento, ejecuta el script de creación de índices:

```bash
# Desde el contenedor Docker
docker exec embalses-backend python scripts/create_indexes.py

# O localmente si tienes Python configurado
cd Backend
python scripts/create_indexes.py
```

Este script crea índices optimizados para:
- **Sensor_Data**: Búsquedas por reservoir y tiempo (queries más frecuentes)
- **alerts**: Alertas activas por nivel y fecha
- **alert_history**: Historial ordenado por fecha
- **users**: Búsqueda por email y rol
- **audit_log**: Auditoría con TTL de 180 días
- **notifications_sent**: Throttling de notificaciones con TTL de 7 días

Los índices mejoran el rendimiento de queries hasta 100x en colecciones grandes.

---

### 7. Verificar Instalación

```bash
# 1. Backend health check
curl http://localhost:8000/health
# Esperado: {"status": "healthy"}

# 2. Verificar conexión MongoDB
docker exec embalses-backend python -c "
from app.config.database import get_database
import asyncio
asyncio.run(get_database())
print('MongoDB conectado')
"

# 3. Verificar frontend
curl -I http://localhost:3000
# Esperado: HTTP/1.1 200 OK
```

---

## Documentación de APIs

### Autenticación

| Método | Endpoint | Descripción | Requiere Auth |
|--------|----------|-------------|---------------|
| `POST` | `/api/auth/login` | Login con email/password, retorna JWT | No |
| `POST` | `/api/auth/logout` | Cerrar sesión (invalida token) | Sí |
| `POST` | `/api/auth/forgot-password` | Solicitar reset de contraseña vía email | No |
| `GET` | `/api/auth/validate-reset-token/{token}` | Validar token de recuperación | No |
| `POST` | `/api/auth/reset-password` | Actualizar contraseña con token | No |

Ejemplo Login:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@embalses.cl&password=Admin123!"
```

---

### Gestión de Usuarios (Solo Admin)

| Método | Endpoint | Descripción | Rol Requerido |
|--------|----------|-------------|---------------|
| `GET` | `/api/users/` | Listar todos los usuarios | Admin |
| `GET` | `/api/users/{user_id}` | Obtener usuario específico | Admin |
| `POST` | `/api/users/` | Crear nuevo usuario | Admin |
| `PUT` | `/api/users/{user_id}` | Actualizar datos de usuario | Admin |
| `DELETE` | `/api/users/{user_id}` | Eliminar usuario permanentemente | Admin |

Ejemplo Crear Usuario:
```bash
curl -X POST "http://localhost:8000/api/users" \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "operario@embalses.cl",
    "password": "Operario123!",
    "full_name": "Juan Pérez",
    "role": "operario"
  }'
```

---

### Sistema de Alertas

| Método | Endpoint | Descripción | Rol Requerido |
|--------|----------|-------------|---------------|
| `GET` | `/api/alerts/` | Obtener alertas activas | Todos |
| `GET` | `/api/alerts/history/` | Historial completo de alertas | Todos |
| `POST` | `/api/alerts/{alert_id}/dismiss` | Marcar alerta como resuelta | Todos |
| `GET` | `/api/alerts/thresholds/` | Obtener configuración de umbrales | Todos |
| `PUT` | `/api/alerts/thresholds/` | Actualizar umbrales | Admin |

Ejemplo Obtener Alertas Activas:
```bash
curl -X GET "http://localhost:8000/api/alerts/" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

Ejemplo Actualizar Umbrales:
```bash
curl -X PUT "http://localhost:8000/api/alerts/thresholds/" \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "ph": {
      "critical_low": 4.5,
      "warning_low": 5.0,
      "warning_high": 5.5,
      "critical_high": 6.5
    },
    "ec": {
      "critical_low": 0.3,
      "warning_low": 0.5,
      "warning_high": 1.2,
      "critical_high": 1.5
    }
  }'
```

---

### Datos de Sensores

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| `GET` | `/api/sensors/latest/` | Última lectura de cada sensor | - |
| `GET` | `/api/sensors/history/` | Datos históricos con filtros | `sensor_type`, `start_date`, `end_date`, `limit` |
| `GET` | `/api/sensors/{sensor_type}/chart/` | Datos formateados para Chart.js | `days` |
| `POST` | `/api/sensors/prediction/` | Obtener predicciones ML | `sensor_type`, `days`, `lookback_days` |
| `POST` | `/api/sensors/prediction-config/` | Actualizar config del modelo | `days`, `lookback_days` |

Ejemplo Obtener Historial:
```bash
curl -X GET "http://localhost:8000/api/sensors/history/?sensor_type=ph&limit=100" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

Ejemplo Predicción ML:
```bash
curl -X POST "http://localhost:8000/api/sensors/prediction/" \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_type": "ph",
    "days": 5,
    "lookback_days": 7
  }'
```

---

### Auditoría

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| `GET` | `/api/audit/logs/` | Obtener historial de auditoría | `action`, `user_email`, `start_date`, `end_date`, `skip`, `limit` |
| `GET` | `/api/audit/actions/` | Listar tipos de acciones disponibles | - |

Ejemplo Filtrar Auditoría:
```bash
curl -X GET "http://localhost:8000/api/audit/logs/?action=login&limit=50" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

---

### 🏥 Health Check

| Método | Endpoint | Descripción | Requiere Auth |
|--------|----------|-------------|---------------|
| `GET` | `/health` | Estado del servidor | ❌ |
| `GET` | `/api/health/database` | Estado de MongoDB | ✅ |

---

### 📄 Documentación Interactiva

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Ambas interfaces permiten probar endpoints directamente desde el navegador.

---

## Estructura del Proyecto

```
UNAB-ProyectoDeTitulo/
├── Backend/                    # API FastAPI + Python
│   ├── main.py                # Servidor principal con todos los endpoints
│   ├── models/                # Modelos de datos y validación
│   ├── certificates/          # Certificados TLS para AWS IoT
│   ├── requirements.txt       # Dependencias de Python
│   └── Dockerfile            # Imagen Docker del backend
├── Frontend/                  # Dashboard Vue.js + TypeScript  
│   ├── src/
│   │   ├── views/            # Páginas principales del sistema
│   │   ├── components/       # Componentes reutilizables
│   │   ├── stores/          # Estado global (Pinia)
│   │   ├── auth/            # Manejo de autenticación
│   │   └── router/          # Configuración de rutas
│   ├── package.json         # Dependencias de Node.js
│   └── Dockerfile          # Imagen Docker del frontend
└── docker-compose.yml      # Orquestación completa del sistema
```

---

## 🔧 Mantenimiento y Operaciones

### Comandos Docker Útiles

```bash
# Ver logs en tiempo real de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Reiniciar un servicio sin afectar los demás
docker-compose restart backend

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ borra datos de MongoDB)
docker-compose down -v

# Reconstruir un servicio específico
docker-compose up -d --build backend

# Limpiar cache de Docker (libera espacio)
docker system prune -a --volumes

# Ver uso de recursos
docker stats
```

---

### Acceso Directo a Servicios

**Backend (Python):**
```bash
# Acceder al contenedor
docker exec -it embalses-backend bash

# Ejecutar comandos Python directamente
docker exec embalses-backend python -c "print('Hello')"

# Ver logs del servidor Uvicorn
docker logs -f embalses-backend
```

**MongoDB:**
```bash
# Acceder a la shell de MongoDB
docker exec -it embalses-mongodb mongosh embalses_iot

# Listar colecciones
show collections

# Ver usuarios
db.users.find().pretty()

# Ver alertas activas
db.alerts.find({status: "active"}).pretty()

# Backup de la base de datos
docker exec embalses-mongodb mongodump --out=/backup

# Restore de la base de datos
docker exec embalses-mongodb mongorestore /backup
```

**Frontend (Nginx):**
```bash
# Acceder al contenedor
docker exec -it embalses-frontend sh

# Ver configuración de Nginx
cat /etc/nginx/nginx.conf

# Reiniciar Nginx
docker exec embalses-frontend nginx -s reload
```

---

### Monitoreo del Sistema

Health Checks:
```bash
# Backend API
curl http://localhost:8000/health

# Frontend
curl -I http://localhost:3000

# MongoDB
docker exec embalses-mongodb mongosh --eval "db.adminCommand('ping')"
```

Verificar Alertas Activas:
```bash
curl -X GET "http://localhost:8000/api/alerts/" \
  -H "Authorization: Bearer {JWT_TOKEN}" | jq
```

Ver Predicciones Recientes:
```bash
curl -X POST "http://localhost:8000/api/sensors/prediction/" \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"sensor_type": "ph", "days": 5, "lookback_days": 7}' | jq
```

---

### Backup y Restauración

Backup Completo de MongoDB:
```bash
# Crear backup
docker exec embalses-mongodb mongodump \
  --db embalses_iot \
  --out /backup/$(date +%Y%m%d_%H%M%S)

# Copiar backup al host
docker cp embalses-mongodb:/backup ./backups/

# Comprimir backup
tar -czf backup_$(date +%Y%m%d).tar.gz ./backups/
```

Restaurar desde Backup:
```bash
# Copiar backup al contenedor
docker cp ./backups/20241103_120000 embalses-mongodb:/backup/

# Restaurar
docker exec embalses-mongodb mongorestore \
  --db embalses_iot \
  /backup/20241103_120000/embalses_iot/
```

---

### Solución de Problemas Comunes

Problema: Backend no inicia
```bash
# Ver logs completos
docker logs embalses-backend --tail 100

# Verificar variables de entorno
docker exec embalses-backend printenv | grep MONGODB

# Verificar conectividad con MongoDB
docker exec embalses-backend python -c "
from app.config.database import get_database
import asyncio
asyncio.run(get_database())
"
```

Problema: No se envían emails
```bash
# Verificar configuración SMTP
docker exec embalses-backend python -c "
from app.config.settings import settings
print(f'SMTP Server: {settings.SMTP_SERVER}')
print(f'SMTP Port: {settings.SMTP_PORT}')
print(f'SMTP User: {settings.SMTP_USERNAME}')
"

# Probar envío manual de email
docker exec embalses-backend python -c "
from app.services.email import send_email
import asyncio
asyncio.run(send_email(
    to_email='test@example.com',
    subject='Test',
    body='Testing email service'
))
"
```

Problema: Frontend muestra "Failed to fetch"
```bash
# Verificar CORS en backend
docker exec embalses-backend python -c "
from main import app
print(app.middleware)
"

# Verificar conectividad
curl http://localhost:8000/health

# Verificar proxy de Nginx
docker exec embalses-frontend cat /etc/nginx/nginx.conf
```

Problema: MongoDB sin espacio
```bash
# Ver uso de disco
docker exec embalses-mongodb df -h

# Limpiar logs antiguos
docker exec embalses-mongodb mongo --eval "
db.adminCommand({ setParameter: 1, logLevel: 1 })
"

# Compactar base de datos
docker exec embalses-mongodb mongo embalses_iot --eval "
db.runCommand({ compact: 'alerts' })
db.runCommand({ compact: 'audit_logs' })
"
```

---

## Testing

### Backend (Pytest)

```bash
# Ejecutar todos los tests
docker exec embalses-backend pytest

# Con cobertura
docker exec embalses-backend pytest --cov=app --cov-report=html

# Tests específicos
docker exec embalses-backend pytest tests/test_auth.py
docker exec embalses-backend pytest tests/test_notifications.py -v

# Modo watch (re-ejecuta al guardar)
docker exec embalses-backend pytest-watch
```

### Frontend (Vitest)

```bash
# Ejecutar tests unitarios
docker exec embalses-frontend npm run test

# Modo watch
docker exec embalses-frontend npm run test:watch

# Con cobertura
docker exec embalses-frontend npm run test:coverage
```

---

## Contribuciones

### Guía de Contribución

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commits descriptivos: `git commit -m "feat: agregar predicción LSTM"`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request con descripción detallada

### Estilo de Código

Backend (Python):
- Seguir PEP 8
- Docstrings en formato Google
- Type hints obligatorios
- Usar Black para formateo: `black .`
- Linting con Flake8: `flake8 app/`

Frontend (TypeScript/Vue):
- Seguir guía de estilo de Vue 3
- ESLint + Prettier configurados
- Composables reutilizables
- Props con tipos explícitos
- Formateo automático: `npm run format`

---

## Autor

Vicente Jara Estay Valdivia
- Ingeniería en Informática - Universidad Andrés Bello
- Email: vjestayvaldivia@gmail.com
- GitHub: @KsmBlitz

---

## Estado del Proyecto

![GitHub last commit](https://img.shields.io/github/last-commit/KsmBlitz/UNAB-ProyectoDeTitulo)
![GitHub issues](https://img.shields.io/github/issues/KsmBlitz/UNAB-ProyectoDeTitulo)
![GitHub stars](https://img.shields.io/github/stars/KsmBlitz/UNAB-ProyectoDeTitulo)

Última actualización: Noviembre 2024  
Versión: 2.0.0 
---

