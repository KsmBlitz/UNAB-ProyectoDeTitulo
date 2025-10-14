# Backend/main.py

# 1. Imports
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated, Optional, List, Any, Dict
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import motor.motor_asyncio
from bson import ObjectId
import asyncio
import logging
import threading

# Importar core_schema y PydanticCustomError para PyObjectId
from pydantic_core import CoreSchema, PydanticCustomError, core_schema

# Importar nuestro cliente AWS IoT
from aws_iot_client import AWSIoTClient, IoTDataProcessor, create_iot_client

# --------------------------------------------------------------------------
# 2. Configuración Centralizada (Lee desde el archivo .env)
# --------------------------------------------------------------------------
class Settings(BaseSettings):
    MONGO_CONNECTION_STRING: str
    DATABASE_NAME: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configuración de email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    
    # Configuración AWS IoT Core
    AWS_IOT_ENDPOINT: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_IOT_ROOT_CA_PATH: str = "./certificates/root-CA.crt"
    AWS_IOT_CERTIFICATE_PATH: str = "./certificates/device.pem.crt"
    AWS_IOT_PRIVATE_KEY_PATH: str = "./certificates/private.pem.key"
    AWS_IOT_TOPIC: str = "sensor/+/data"
    AWS_IOT_CLIENT_ID: str = "FastAPI_Consumer"

    # ✅ MEJOR: Usar la clase Config tradicional
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings() # type: ignore

# --------------------------------------------------------------------------
# 3. Conexión a la Base de Datos
# --------------------------------------------------------------------------
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING)
db = client[settings.DATABASE_NAME]
users_collection = db.users
sensor_collection = db.Sensor_Data

# --------------------------------------------------------------------------
# 4. Modelos de Datos (Pydantic v2)
# --------------------------------------------------------------------------

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> CoreSchema:
        def validate_from_str(input_value: str) -> ObjectId:
            if not ObjectId.is_valid(input_value):
                raise PydanticCustomError("object_id", "Invalid ObjectId")
            return ObjectId(input_value)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_after_validator_function(validate_from_str, core_schema.str_schema())
            ]),
            serialization=core_schema.to_string_ser_schema(),
        )

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "operario"
    disabled: Optional[bool] = False

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None

class UserPublic(UserBase):
    id: PyObjectId = Field(alias='_id')
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class UserCreate(UserBase):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# NUEVO: Modelo para datos de sensores desde AWS IoT Core
class SensorData(BaseModel):
    reservoirId: str
    temperature: float
    ec: float
    ph: Optional[float] = None
    timestamp: Optional[str] = None

# --------------------------------------------------------------------------
# 5. Utilidades y Dependencias de Seguridad
# --------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se pudieron validar las credenciales", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await users_collection.find_one({"email": email})
    if user is None: raise credentials_exception
    return user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos de administrador requeridos")
    return current_user

# --------------------------------------------------------------------------
# 6. Inicialización de la App FastAPI
# --------------------------------------------------------------------------
app = FastAPI(title="API para Dashboard de Embalses IoT", version="1.0.0")

# Configuración de CORS para permitir ngrok y desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174",  # Puerto donde está ejecutándose el frontend
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",  # También para 127.0.0.1
        "https://unconical-wavily-jefferey.ngrok-free.dev"  # Tu URL de ngrok
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --------------------------------------------------------------------------
# AWS IoT Core Integration
# --------------------------------------------------------------------------
# Variables globales para el cliente IoT
iot_client: Optional[AWSIoTClient] = None
iot_processor = IoTDataProcessor()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def save_sensor_data_to_db(sensor_data: dict):
    """Guarda los datos del sensor en MongoDB de forma asíncrona"""
    try:
        # Procesar los datos del sensor
        processed_data = iot_processor.process_sensor_message(sensor_data)
        
        # Insertar en MongoDB
        result = await sensor_collection.insert_one(processed_data)
        logger.info(f"✅ Datos guardados en MongoDB con ID: {result.inserted_id}")
        
    except Exception as e:
        logger.error(f"❌ Error guardando datos en DB: {e}")

def on_iot_message_received(sensor_data: dict):
    """Callback para procesar mensajes de AWS IoT Core"""
    logger.info(f"📡 Mensaje IoT recibido: {sensor_data}")
    
    # Actualizar actividad del sensor
    reservoir_id = sensor_data.get('reservoirId', 'unknown')
    if reservoir_id != 'unknown':
        asyncio.create_task(update_sensor_activity(reservoir_id))
    
    # Ejecutar la función de guardado en un hilo separado
    threading.Thread(
        target=save_sensor_data_sync,
        args=(sensor_data,),
        daemon=True
    ).start()

def save_sensor_data_sync(sensor_data: dict):
    """Versión sincrónica para guardar datos del sensor"""
    try:
        # Procesar los datos del sensor
        processed_data = iot_processor.process_sensor_message(sensor_data)
        
        # Usar pymongo directamente (síncrono) en lugar de motor (asíncrono)
        import pymongo
        
        # Crear conexión síncrona temporal
        sync_client = pymongo.MongoClient(settings.MONGO_CONNECTION_STRING)
        sync_db = sync_client[settings.DATABASE_NAME]
        sync_collection = sync_db.Sensor_Data
        
        # Insertar directamente
        result = sync_collection.insert_one(processed_data)
        logger.info(f"✅ Datos guardados en MongoDB con ID: {result.inserted_id}")
        
        # Cerrar conexión
        sync_client.close()
        
    except Exception as e:
        logger.error(f"❌ Error guardando datos en DB: {e}")

def start_iot_connection():
    """Inicia la conexión con AWS IoT Core en un hilo separado"""
    global iot_client
    
    try:
        logger.info("🚀 Iniciando conexión con AWS IoT Core...")
        
        # Crear el cliente IoT
        iot_client = create_iot_client(settings)
        iot_client.set_message_callback(on_iot_message_received)
        
        # Conectar
        if iot_client.connect():
            # Suscribirse al tópico de sensores
            if iot_client.subscribe_to_topic(settings.AWS_IOT_TOPIC):
                logger.info(f"✅ AWS IoT Core configurado exitosamente. Escuchando: {settings.AWS_IOT_TOPIC}")
            else:
                logger.error("❌ Error suscribiéndose al tópico IoT")
        else:
            logger.error("❌ Error conectando con AWS IoT Core")
            
    except Exception as e:
        logger.error(f"❌ Error iniciando AWS IoT: {e}")

@app.on_event("startup")
async def startup_event():
    """Eventos que se ejecutan al iniciar la aplicación"""
    logger.info("🚀 Iniciando API para Dashboard de Embalses IoT")
    
    # Iniciar conexión IoT en un hilo separado para no bloquear la API
    threading.Thread(target=start_iot_connection, daemon=True).start()
    
    # Iniciar monitoreo de sensores en background
    asyncio.create_task(check_sensor_timeouts())
    logger.info("⏰ Sistema de monitoreo de sensores iniciado")

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos que se ejecutan al cerrar la aplicación"""
    logger.info("🛑 Cerrando aplicación...")
    
    global iot_client
    if iot_client:
        iot_client.disconnect()
        logger.info("✅ Conexión IoT cerrada correctamente")

# --------------------------------------------------------------------------
# Sistema de Monitoreo de Sensores
# --------------------------------------------------------------------------

# Registro de última actividad de sensores
sensor_last_seen: Dict[str, datetime] = {}
sensor_status: Dict[str, str] = {}  # "online", "warning", "offline"

# Configuración de timeouts (en segundos)
SENSOR_WARNING_TIMEOUT = 15 * 60  # 15 minutos = warning
SENSOR_OFFLINE_TIMEOUT = 30 * 60  # 30 minutos = offline
SENSOR_CHECK_INTERVAL = 60        # Revisar cada 60 segundos

async def update_sensor_activity(reservoir_id: str):
    """Actualiza la última actividad de un sensor"""
    global sensor_last_seen, sensor_status
    
    current_time = datetime.now(timezone.utc)
    sensor_last_seen[reservoir_id] = current_time
    
    # Si estaba offline/warning y ahora recibió datos, marcarlo como online
    if sensor_status.get(reservoir_id) != "online":
        sensor_status[reservoir_id] = "online"
        logger.info(f"🟢 Sensor {reservoir_id} recuperado - Estado: ONLINE")

async def check_sensor_timeouts():
    """Tarea en background que verifica timeouts de sensores"""
    global sensor_last_seen, sensor_status
    
    while True:
        try:
            current_time = datetime.now(timezone.utc)
            
            for reservoir_id, last_seen in list(sensor_last_seen.items()):
                time_since_last_seen = (current_time - last_seen).total_seconds()
                current_status = sensor_status.get(reservoir_id, "unknown")
                
                new_status = None
                
                if time_since_last_seen > SENSOR_OFFLINE_TIMEOUT:
                    # 30+ minutos sin datos = OFFLINE
                    if current_status != "offline":
                        new_status = "offline"
                        logger.warning(f"🔴 Sensor {reservoir_id} DESCONECTADO - Sin datos por {int(time_since_last_seen/60)} minutos")
                        
                elif time_since_last_seen > SENSOR_WARNING_TIMEOUT:
                    # 15-30 minutos sin datos = WARNING
                    if current_status not in ["offline", "warning"]:
                        new_status = "warning"
                        logger.warning(f"🟡 Sensor {reservoir_id} en ADVERTENCIA - Sin datos por {int(time_since_last_seen/60)} minutos")
                
                # Actualizar estado si cambió
                if new_status:
                    sensor_status[reservoir_id] = new_status
                    
                    # Guardar evento en base de datos
                    await save_sensor_status_event(reservoir_id, new_status, time_since_last_seen)
            
            # Esperar antes del próximo chequeo
            await asyncio.sleep(SENSOR_CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"❌ Error en monitoreo de sensores: {e}")
            await asyncio.sleep(SENSOR_CHECK_INTERVAL)

async def save_sensor_status_event(reservoir_id: str, status: str, time_inactive: float):
    """Guarda un evento de cambio de estado del sensor"""
    try:
        # Crear colección de eventos si no existe
        events_collection = db.Sensor_Events
        
        event_document = {
            "reservoirId": reservoir_id,
            "sensorId": f"AWS_IoT_{reservoir_id}",
            "event_type": "status_change",
            "new_status": status,
            "previous_status": sensor_status.get(reservoir_id, "unknown"),
            "time_inactive_minutes": int(time_inactive / 60),
            "timestamp": datetime.now(timezone.utc),
            "message": f"Sensor {status} - Sin actividad por {int(time_inactive/60)} minutos" if status != "online" else "Sensor recuperado"
        }
        
        result = await events_collection.insert_one(event_document)
        logger.info(f"📝 Evento de sensor guardado: {reservoir_id} -> {status}")
        
    except Exception as e:
        logger.error(f"❌ Error guardando evento de sensor: {e}")

# --------------------------------------------------------------------------
# 7. Endpoints de la API
# --------------------------------------------------------------------------
@app.get("/", tags=["Root"])
def read_root():
    global iot_client
    iot_status = "Conectado" if iot_client and iot_client.is_connected else "Desconectado"
    return {
        "status": "Servidor FastAPI conectado y con autenticación",
        "aws_iot_status": iot_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/iot/status", tags=["AWS IoT"])
async def get_iot_status():
    """Obtiene el estado actual de la conexión AWS IoT Core"""
    global iot_client
    
    if not iot_client:
        return {
            "connected": False,
            "status": "Cliente IoT no inicializado",
            "endpoint": settings.AWS_IOT_ENDPOINT,
            "topic": settings.AWS_IOT_TOPIC
        }
    
    return {
        "connected": iot_client.is_connected,
        "status": "Conectado" if iot_client.is_connected else "Desconectado",
        "endpoint": settings.AWS_IOT_ENDPOINT,
        "topic": settings.AWS_IOT_TOPIC,
        "client_id": settings.AWS_IOT_CLIENT_ID,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/token", response_model=Token, tags=["Autenticación"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos")
    access_token = create_access_token(
        data={"sub": user["email"], "role": user.get("role"), "full_name": user.get("full_name")}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users", response_model=List[UserPublic], tags=["Usuarios"])
async def read_users(admin_user: dict = Depends(get_current_admin_user)):
    users_from_db = await users_collection.find().to_list(1000)
    return [UserPublic(**user) for user in users_from_db]

@app.post("/api/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED, tags=["Usuarios"])
async def create_user(user: UserCreate, admin_user: dict = Depends(get_current_admin_user)):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user: raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={"password"})
    user_data["hashed_password"] = hashed_password
    new_user_doc = await users_collection.insert_one(user_data)
    created_user_from_db = await users_collection.find_one({"_id": new_user_doc.inserted_id})
    if created_user_from_db is None:
        raise HTTPException(status_code=500, detail="Error al crear el usuario")
    return UserPublic(**created_user_from_db)

@app.put("/api/users/{user_id}", response_model=UserPublic, tags=["Usuarios"])
async def update_user(user_id: str, user_update: UserUpdate, admin_user: dict = Depends(get_current_admin_user)):
    if not ObjectId.is_valid(user_id): raise HTTPException(status_code=400, detail="El ID de usuario no es válido")
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_data: raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    
    result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    if result.matched_count == 0: raise HTTPException(status_code=404, detail="No se encontró el usuario")
    
    updated_user_from_db = await users_collection.find_one({"_id": ObjectId(user_id)})
    if updated_user_from_db is None:
        raise HTTPException(status_code=404, detail="No se encontró el usuario después de actualizar")
    return UserPublic(**updated_user_from_db)

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Usuarios"])
async def delete_user(user_id: str, admin_user: dict = Depends(get_current_admin_user)):
    if not ObjectId.is_valid(user_id): raise HTTPException(status_code=400, detail="El ID de usuario no es válido")
    if str(admin_user["_id"]) == user_id: raise HTTPException(status_code=403, detail="Un administrador no puede eliminarse a sí mismo")
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0: raise HTTPException(status_code=404, detail="No se encontró el usuario a eliminar")
    return

@app.get("/api/metrics/latest", tags=["Datos de Sensores"])
async def get_latest_metrics(current_user: dict = Depends(get_current_user)):
    latest_reading = await sensor_collection.find_one({}, sort=[("ReadTime", -1)])
    if not latest_reading: 
        raise HTTPException(status_code=404, detail="No se encontraron lecturas de sensores")
    
    return {
        "temperatura_agua": {
            "value": round(latest_reading.get("Temperature", 0), 1), 
            "unit": "°C", 
            "changeText": "Temperatura del agua", # ✅ CAMBIO: Quitar referencia al ESP32
            "isPositive": True,
            "status": "normal"
        },
        "ph": {
            "value": round(latest_reading.get("pH_Value", 7.0), 1), 
            "unit": "", 
            "changeText": "Nivel de acidez", 
            "isPositive": True,
            "status": "normal" if 6.5 <= latest_reading.get("pH_Value", 7.0) <= 8.5 else "warning"
        },
        "conductividad": {
            "value": round(latest_reading.get("EC", 0), 2), 
            "unit": "dS/m", 
            "changeText": "Conductividad eléctrica", 
            "isPositive": True,
            "status": "normal"
        },
        "nivel_agua": {
            "value": round(latest_reading.get("Water_Level", 0), 1), 
            "unit": "m", 
            "changeText": "Nivel del embalse", 
            "isPositive": True,
            "status": "normal"
        }
    }

@app.get("/api/charts/historical-data", tags=["Datos de Sensores"])
async def get_historical_data(
    sensor_type: str = "all",  # ph, temperatura, conductividad, nivel, all
    hours: int = 24,  # últimas X horas, 0 = todos los datos
    current_user: dict = Depends(get_current_user)
):
    """Obtener datos históricos de sensores para gráficos"""
    
    try:
        # Si hours es 0, obtener todos los datos
        if hours == 0:
            # Obtener todos los datos (limitado a los últimos 1000 registros por rendimiento)
            cursor = sensor_collection.find({}, sort=[("ReadTime", 1)]).limit(1000)
        else:
            # Calcular fecha de inicio
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            # Consulta a la base de datos
            cursor = sensor_collection.find(
                {"ReadTime": {"$gte": start_time, "$lte": end_time}},
                sort=[("ReadTime", 1)]
            ).limit(500)  # Limitar para rendimiento
        
        readings = await cursor.to_list(length=1000)
        
        if not readings:
            raise HTTPException(status_code=404, detail="No hay datos en el rango solicitado")
        
        # Formatear datos con mejor formato de fecha
        if hours <= 24:
            # Para rangos cortos, mostrar hora:minuto
            labels = [r["ReadTime"].strftime("%H:%M") for r in readings]
        elif hours <= 168:  # 7 días
            # Para semana, mostrar día/mes hora
            labels = [r["ReadTime"].strftime("%d/%m %H:%M") for r in readings]
        else:
            # Para rangos largos, mostrar día/mes/año
            labels = [r["ReadTime"].strftime("%d/%m/%Y") for r in readings]
        
        result = {
            "labels": labels,
            "timestamps": [r["ReadTime"].isoformat() for r in readings],
        }
        
        # ✅ Usar los nombres correctos de campos de tu base de datos
        if sensor_type == "all" or sensor_type == "ph":
            result["ph"] = [round(r.get("pH_Value", 0), 2) for r in readings]
        
        if sensor_type == "all" or sensor_type == "temperatura":
            result["temperatura"] = [round(r.get("Temperature", 0), 1) for r in readings]
        
        if sensor_type == "all" or sensor_type == "conductividad":
            result["conductividad"] = [round(r.get("EC", 0), 2) for r in readings]
        
        if sensor_type == "all" or sensor_type == "nivel":
            result["nivel_agua"] = [round(r.get("Water_Level", 0), 1) for r in readings]
        
        return result
        
    except Exception as e:
        logger.error(f"Error en historical-data: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener datos históricos: {str(e)}")

@app.get("/api/charts/water-level", tags=["Datos de Sensores"])
async def get_water_level_data(
    current_user: dict = Depends(get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None
):
    """
    Obtiene registros para el gráfico de nivel de agua.
    Puede filtrar por un rango de fechas o devolver los últimos 'limit' registros.
    """
    query = {}
    if start_date and end_date:
        query["ReadTime"] = {"$gte": start_date, "$lte": end_date}
    
    sort_order = [("ReadTime", 1)] if start_date else [("ReadTime", -1)]

    cursor = sensor_collection.find(query).sort(sort_order)

    if limit and not start_date:
        cursor = cursor.limit(limit)

    readings = await cursor.to_list(length=1000)
    
    if not start_date and readings:
        readings.reverse()

    if not readings:
        raise HTTPException(status_code=404, detail="No hay datos para el rango seleccionado")

    first_time = readings[0]["ReadTime"]
    last_time = readings[-1]["ReadTime"]
    data_range_seconds = (last_time - first_time).total_seconds()

    time_format = "%d-%b %H:%M" if data_range_seconds <= (24 * 3600 * 2) else "%d-%b-%Y"

    # *** IMPORTANTE: AJUSTA ESTE CAMPO ***
    water_level_field = "Potassium"
    
    return {
        "labels": [r["ReadTime"].strftime(time_format) for r in readings],
        "real_level": [r.get(water_level_field, 0) for r in readings],
        "expected_level": [r.get(water_level_field, 0) + 5 for r in readings]
    }

# NUEVO: Endpoint para recibir datos de sensores desde AWS IoT Core
@app.post("/api/sensors/data", status_code=status.HTTP_201_CREATED, tags=["Datos de Sensores"])
async def receive_sensor_data(data: SensorData):
    """
    Endpoint para recibir datos de sensores desde AWS IoT Core.
    """
    try:
        # Prepara el documento para insertar en MongoDB
        sensor_document = {
            "reservoirId": data.reservoirId,
            "Temperature": data.temperature,
            "EC": data.ec,
            "pH_Value": data.ph,
            "ReadTime": datetime.now(timezone.utc),
            # Agregar campos adicionales para mantener compatibilidad
            "SensorID": f"AWS_IoT_{data.reservoirId}",
            "Timestamp": data.timestamp or datetime.now(timezone.utc).isoformat()
        }

        # Inserta el documento en la colección 'Sensor_Data'
        result = await sensor_collection.insert_one(sensor_document)
        print(f"Datos del embalse '{data.reservoirId}' guardados con ID: {result.inserted_id}")

        return {
            "status": "Datos recibidos y guardados exitosamente",
            "reservoirId": data.reservoirId,
            "insertedId": str(result.inserted_id)
        }

    except Exception as e:
        print(f"Error al guardar datos de sensor: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al procesar los datos del sensor: {str(e)}"
        )

@app.get("/api/sensors/status", tags=["Datos de Sensores"])
async def get_sensors_status(current_user: dict = Depends(get_current_user)):
    """Obtiene el estado actual de todos los sensores"""
    
    current_time = datetime.now(timezone.utc)
    sensors_info = []
    
    for reservoir_id, last_seen in sensor_last_seen.items():
        time_since_last_seen = (current_time - last_seen).total_seconds()
        status = sensor_status.get(reservoir_id, "unknown")
        
        # Obtener última lectura de datos del sensor
        latest_reading = await sensor_collection.find_one(
            {"reservoirId": reservoir_id}, 
            sort=[("ReadTime", -1)]
        )
        
        sensor_info = {
            "reservoir_id": reservoir_id,
            "sensor_id": f"AWS_IoT_{reservoir_id}",
            "status": status,
            "last_seen": last_seen.isoformat(),
            "minutes_since_last_data": int(time_since_last_seen / 60),
            "last_values": {
                "temperature": latest_reading.get("Temperature", 0) if latest_reading else 0,
                "ph": latest_reading.get("pH_Value", 7.0) if latest_reading else 7.0,
                "ec": latest_reading.get("EC", 0) if latest_reading else 0,
                "water_level": latest_reading.get("Water_Level", 0) if latest_reading else 0
            } if latest_reading else None
        }
        
        sensors_info.append(sensor_info)
    
    # Estadísticas resumidas
    total_sensors = len(sensors_info)
    online_count = sum(1 for s in sensors_info if s["status"] == "online")
    warning_count = sum(1 for s in sensors_info if s["status"] == "warning")
    offline_count = sum(1 for s in sensors_info if s["status"] == "offline")
    
    return {
        "summary": {
            "total": total_sensors,
            "online": online_count,
            "warning": warning_count,
            "offline": offline_count
        },
        "sensors": sensors_info,
        "timestamp": current_time.isoformat()
    }

@app.get("/api/sensors/events", tags=["Datos de Sensores"])
async def get_sensor_events(
    reservoir_id: Optional[str] = None,
    hours: int = 24,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene eventos de sensores (conexiones/desconexiones)"""
    
    # Filtros de consulta
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)
    
    query: Dict[str, Any] = {"timestamp": {"$gte": start_time, "$lte": end_time}}
    if reservoir_id:
        query["reservoirId"] = reservoir_id
    
    # Buscar eventos
    events_collection = db.Sensor_Events
    events_cursor = events_collection.find(query).sort("timestamp", -1).limit(100)
    events = await events_cursor.to_list(length=100)
    
    return {
        "events": events,
        "filters": {
            "reservoir_id": reservoir_id,
            "hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    }

@app.get("/api/sensors/individual", tags=["Datos de Sensores"])
async def get_individual_sensors_status(current_user: dict = Depends(get_current_user)):
    """Estado detallado de cada sensor individual (actualizado)"""
    
    try:
        current_time = datetime.now(timezone.utc)
        sensors = []
        
        # ✅ CAMBIO 1: Si no hay sensores en memoria, buscar SOLO en la base de datos
        # Buscar sensores únicos en la base de datos
        pipeline = [
            {"$sort": {"ReadTime": -1}},
            {"$group": {
                "_id": "$reservoirId", 
                "lastReading": {"$first": "$$ROOT"}
            }},
            {"$limit": 20}
        ]
        
        db_sensors = await sensor_collection.aggregate(pipeline).to_list(length=None)
        
        for sensor_group in db_sensors:
            reservoir_id = sensor_group["_id"]
            latest_reading = sensor_group["lastReading"]
            
            # ✅ ARREGLO: Asegurar que ambas fechas tengan zona horaria
            last_reading_time = latest_reading["ReadTime"]
            if last_reading_time.tzinfo is None:
                last_reading_time = last_reading_time.replace(tzinfo=timezone.utc)
            
            time_diff = (current_time - last_reading_time).total_seconds()
            minutes_diff = time_diff / 60
            
            # Determinar estado basado en tiempo
            if minutes_diff < 15:
                status = "online"
            elif minutes_diff < 30:
                status = "warning"  
            else:
                status = "offline"
            
            # ✅ CAMBIO 2: Formato más simple para la tabla
            sensor_data = {
                "uid": reservoir_id,  # UID del sensor
                "last_value": {
                    "value": round(latest_reading.get("Temperature", 0), 1),
                    "unit": "°C",
                    "type": "Temperatura"
                },
                "status": status,
                "location": f"Embalse {reservoir_id}",
                "last_reading": last_reading_time.isoformat(),
                "minutes_since_reading": int(minutes_diff)
            }
            
            sensors.append(sensor_data)
        
        return sensors
        
    except Exception as e:
        logger.error(f"Error obteniendo sensores individuales: {e}")
        # ✅ CAMBIO 3: Retornar lista vacía en lugar de error HTTP
        return []
