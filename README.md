# Dashboard IoT para Monitoreo de Embalses

![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb)
![MQTT](https://img.shields.io/badge/MQTT-660066?logo=mqtt)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker)

Sistema de monitoreo IoT full-stack diseñado para la agricultura de precisión. Este proyecto provee una solución completa para la recolección, almacenamiento, procesamiento y visualización de datos de sensores ubicados en embalses de agua para cultivos de arándanos.

El objetivo es ofrecer una herramienta centralizada que permita a los operarios tomar decisiones basadas en datos para optimizar el uso de recursos hídricos, predecir tendencias y actuar de forma proactiva ante posibles problemas.

---

## 📊 Estado del Proyecto (MVP Funcional)

Actualmente, el proyecto se encuentra en una fase de **Producto Mínimo Viable (MVP) completamente funcional**. La arquitectura full-stack está establecida y las características principales de autenticación, gestión y visualización de datos están implementadas y conectadas.

## 🖼️ Vista Previa del Dashboard


![Dashboard](https://blogger.googleusercontent.com/img/a/AVvXsEiQlu2xNAXmpjktZ1rleeE2c_unHYeQf4hQWCBjerEQ-PCCf27yN1KMtS1bhu2NQ4gZ0UI-ukPz4nbGGBF998TPSAhGSoQvKY9JmOiTydXbq3GUkMF_2psk-B5VvJKcHXsn1fYePiS5Z5ML48KkSgM4PxGGgieRlV83FbN4Te1R3u-oNha8iL8ZXSTV7FSi)

---

## 🏗️ Diagrama de Arquitectura

El sistema está compuesto por varios servicios que se comunican entre sí. La arquitectura está diseñada para ser escalable y desplegable a través de Docker.


<img width="1048" height="953" alt="image" src="https://github.com/user-attachments/assets/1a876814-8bb4-4074-bcfa-0d846f5fbc25" />

---

## ✨ Características Implementadas

* **Autenticación Segura:** Flujo de login completo con tokens JWT, hashing de contraseñas (`bcrypt`) y persistencia de sesión.
* **Gestión de Usuarios (CRUD):** Interfaz completa para crear, leer, editar y eliminar usuarios.
* **Autorización por Roles (RBAC):** El sistema distingue entre roles de "Administrador" y "Operario", restringiendo el acceso a secciones específicas.
* **Dashboard Dinámico:** Las tarjetas de métricas (`Temperatura`, `pH`, etc.) se conectan y muestran datos en tiempo real desde el backend.
* **Layout Profesional:** Interfaz con barra de navegación lateral colapsable y header con menú de usuario interactivo.
* **Visualización de Datos (Base):** Componentes de gráficos y tablas listos y visualmente completos, usando `Chart.js`.
* **Backend Robusto:** API RESTful con FastAPI que se conecta de forma segura a una base de datos en la nube (MongoDB Atlas) usando variables de entorno.

---

## 🛠️ Tecnologías Utilizadas

| Área                 | Tecnología                                               |
| -------------------- | -------------------------------------------------------- |
| **Frontend** | Vue 3 (Composition API), TypeScript, Vite, Chart.js, PrimeIcons |
| **Backend** | Python 3, FastAPI, Pydantic, Uvicorn, Motor, Passlib, python-jose |
| **Base de Datos** | MongoDB Atlas (Cloud)                                    |
| **Comunicación IoT** | MQTT (Arquitectura definida)                             |
| **Machine Learning** | (Arquitectura definida para SVM/XGBoost)                 |
| **DevOps** | Docker, Docker Compose (Arquitectura definida)           |
| **Calidad de Código** | ESLint, Prettier                                         |

---

## 🚀 Instalación y Puesta en Marcha

### Manualmente (Para Desarrollo)

Asegúrate de tener un archivo `.env` en la carpeta `backend` con tu `MONGO_CONNECTION_STRING` y demás secretos.

1.  **Backend (FastAPI):**
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```
2.  **Frontend (Vue):**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

### Con Docker (Próximo Paso)

El archivo `docker-compose.yml` está planificado para orquestar todos los servicios.

---

## 📁 Estructura del Repositorio

/
├── backend/          # Código del servicio FastAPI (Python)
├── frontend/         # Código de la aplicación Vue.js
└── README.md         # Este archivo


---

## 📝 Próximos Pasos

Con la base de la aplicación ya construida y funcional, los siguientes pasos se centran en la ingesta de datos en tiempo real y la inteligencia del sistema.

* [ ] **Conectar Gráficos y Tabla a la API:** Reemplazar los datos de ejemplo de los gráficos y la tabla con datos reales servidos por nuevos endpoints del backend.
* [ ] **Implementar Suscriptor MQTT:** Crear el script en el backend que se conecte al broker MQTT, reciba los datos de los sensores y los guarde en MongoDB.
* [ ] **Integrar Modelo de Machine Learning:** Entrenar un modelo de predicción (SVM/XGBoost) y crear un endpoint en la API para servir sus resultados.
* [ ] **Dockerización Completa:** Crear los `Dockerfile` para cada servicio y un `docker-compose.yml` para levantar todo el entorno con un solo comando.
* [ ] **Pulir Diseño Responsivo:** Realizar pruebas exhaustivas y ajustes finales en la interfaz para mejorar la experiencia en dispositivos móviles.


