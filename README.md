# Sistema IoT de Monitoreo de Calidad del Agua para Arándanos

![Vue.js](https://img.shields.io/badge/Vue.js-3.5-4FC08D?logo=vue.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?logo=docker&logoColor=white)
![ML](https://img.shields.io/badge/ML-Scikit--learn-F7931E?logo=scikit-learn&logoColor=white)
![Status](https://img.shields.io/badge/Status-Producci%C3%B3n-success)

---

## Resumen

Plataforma IoT empresarial para monitoreo inteligente de calidad del agua en embalses de arándanos en Chile. Integra sensores en tiempo real con AWS IoT Core, predicción ML, sistema de alertas multinivel y auditoría completa. Arquitectura moderna basada en microservicios, con backend FastAPI y frontend Vue 3.

---

## Características Principales

- Monitoreo en tiempo real de pH, conductividad, temperatura y nivel de agua
- Predicción inteligente con Machine Learning (regresión lineal)
- Sistema de alertas proactivo con notificaciones automáticas (Email/WhatsApp)
- Gestión de usuarios con roles (Admin/Operario) y autenticación JWT
- Auditoría completa de todas las acciones críticas
- Visualización avanzada con gráficos históricos y tendencias predictivas
- Arquitectura escalable y segura con Docker, MongoDB y Redis

---

## Arquitectura

```
UNAB-ProyectoDeTitulo/
├── Backend/      # API REST FastAPI
│   ├── app/
│   │   ├── models/       # Modelos de datos
│   │   ├── routes/       # Endpoints API
│   │   ├── services/     # Lógica de negocio
│   │   ├── repositories/ # Acceso a datos
│   │   ├── middleware/   # Middlewares
│   │   └── utils/        # Utilidades
│   ├── tests/            # Tests unitarios
│   └── Dockerfile
├── Frontend/     # Dashboard Vue.js
│   ├── src/
│   │   ├── components/   # Componentes
│   │   ├── views/        # Vistas
│   │   ├── stores/       # Estado global
│   │   ├── auth/         # Autenticación
│   │   └── router/       # Rutas
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml    # Orquestación
└── README.md             # Este archivo
```

---

## Instalación y Despliegue

### Prerrequisitos

- Docker 24.0+ y Docker Compose 2.0+
- Git
- Cuenta Gmail o SMTP para emails
- (Opcional) AWS IoT Core configurado

### 1. Clonar el Repositorio

```bash
git clone https://github.com/KsmBlitz/UNAB-ProyectoDeTitulo.git
cd UNAB-ProyectoDeTitulo
```

### 2. Configurar Variables de Entorno

Crear archivo `.env` en `Backend/` y `Frontend/` según los ejemplos provistos.

### 3. Despliegue con Docker

```bash
docker-compose up -d --build
```

### 4. Acceso al Sistema

| Servicio         | URL                        | Descripción           |
|------------------|----------------------------|-----------------------|
| Frontend         | http://localhost:3000      | Dashboard principal   |
| Backend API      | http://localhost:8000      | API REST              |
| Swagger Docs     | http://localhost:8000/docs | Documentación API     |
| MongoDB          | localhost:27017            | Base de datos         |

---

## Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f
# Reiniciar backend
docker-compose restart backend
# Detener todos los servicios
docker-compose down
# Acceder al contenedor backend
docker exec -it embalses-backend bash
# Acceder a MongoDB
docker exec -it embalses-mongodb mongosh embalses_iot
```

---

## Testing

### Backend (Pytest)

```bash
docker exec embalses-backend pytest
docker exec embalses-backend pytest --cov=app --cov-report=html
```

### Frontend (Vitest)

```bash
docker exec embalses-frontend npm run test
```

---

## Tecnologías

| Categoría      | Tecnologías principales |
|----------------|------------------------|
| Frontend       | Vue 3, TypeScript, Vite, Tailwind CSS |
| Backend        | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| Base de Datos  | MongoDB 7.0, Motor (async) |
| ML/Predicción  | Scikit-learn, NumPy |
| Autenticación  | JWT, bcrypt, OAuth2 |
| IoT            | AWS IoT Core, MQTT, TLS |
| Notificaciones | Gmail SMTP, WhatsApp Business API |
| DevOps         | Docker, Docker Compose, Nginx |
| Testing        | Pytest, Pytest-asyncio, Vitest |
| Calidad Código | ESLint, Prettier, Black |

---

## Guía de Contribución

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commits descriptivos: `git commit -m "feat: agregar predicción LSTM"`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request con descripción detallada

### Estilo de Código

**Backend (Python):**
- PEP 8, docstrings Google, type hints
- Black para formateo: `black .`
- Linting: `flake8 app/`

**Frontend (TypeScript/Vue):**
- Guía de estilo Vue 3
- ESLint + Prettier
- Props con tipos explícitos
- Formateo: `npm run format`

---

## Autor

Vicente Estay Valdivia
Ingeniería en Computación e Informática - Universidad Andrés Bello
Email: vjestayvaldivia@gmail.com
GitHub: [@KsmBlitz](https://github.com/KsmBlitz)

---

## Estado del Proyecto

![GitHub last commit](https://img.shields.io/github/last-commit/KsmBlitz/UNAB-ProyectoDeTitulo)
![GitHub issues](https://img.shields.io/github/issues/KsmBlitz/UNAB-ProyectoDeTitulo)
![GitHub stars](https://img.shields.io/github/stars/KsmBlitz/UNAB-ProyectoDeTitulo)

Última actualización: Noviembre 2025  
Versión: 2.0.0

