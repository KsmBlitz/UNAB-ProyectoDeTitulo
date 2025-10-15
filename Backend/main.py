# Backend/main.py

# 1. Imports
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic_settings import BaseSettings
from typing import Annotated, Optional, List, Dict
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import motor.motor_asyncio
from bson import ObjectId
import asyncio
import threading
import logging
from collections import defaultdict

# Importar core_schema y PydanticCustomError para PyObjectId
from pydantic_core import CoreSchema, PydanticCustomError, core_schema

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 2. Configuración Centralizada (Lee desde el archivo .env)
# --------------------------------------------------------------------------
class Settings(BaseSettings):
    # Variables básicas requeridas
    MONGO_CONNECTION_STRING: str
    DATABASE_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # Variables opcionales para AWS IoT (pueden estar en .env pero no son requeridas)
    smtp_server: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    aws_iot_endpoint: Optional[str] = None
    aws_region: Optional[str] = None
    aws_iot_root_ca_path: Optional[str] = None
    aws_iot_certificate_path: Optional[str] = None
    aws_iot_private_key_path: Optional[str] = None
    aws_iot_topic: Optional[str] = None
    aws_iot_client_id: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignorar variables extra del .env

settings = Settings() # type: ignore

# --------------------------------------------------------------------------
# 3. Conexión a la Base de Datos
# --------------------------------------------------------------------------
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING)
db = client[settings.DATABASE_NAME]
users_collection = db.users
sensor_collection = db.Sensor_Data

# --------------------------------------------------------------------------
# 4. Modelos de Datos (Pydantic) - CON LA CORRECCIÓN FINAL PARA ObjectId
# --------------------------------------------------------------------------

# Clase PyObjectId personalizada para Pydantic v2
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler) -> CoreSchema:
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
    role: str
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

# --------------------------------------------------------------------------
# 5. Sistema de Monitoreo de Sensores
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

def on_iot_message_received(sensor_data: dict):
    """Callback para procesar mensajes de AWS IoT Core"""
    logger.info(f"📡 Mensaje IoT recibido: {sensor_data}")
    
    # Actualizar actividad del sensor
    reservoir_id = sensor_data.get('reservoirId', 'unknown')
    if reservoir_id != 'unknown':
        asyncio.create_task(update_sensor_activity(reservoir_id))

def start_iot_connection():
    """Inicia la conexión con AWS IoT Core"""
    try:
        # Aquí se conectaría con AWS IoT Core
        logger.info("🔗 Conectando con AWS IoT Core...")
        # aws_iot_client.connect(on_message_callback=on_iot_message_received)
    except Exception as e:
        logger.error(f"❌ Error conectando con AWS IoT Core: {e}")

# --------------------------------------------------------------------------
# 6. Utilidades y Dependencias de Seguridad
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
        email: str = payload.get("sub") # type: ignore
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
# 7. Inicialización de la App FastAPI
# --------------------------------------------------------------------------
app = FastAPI(title="API para Dashboard de Embalses IoT", version="1.0.0")
app.add_middleware(
    CORSMiddleware, 
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:4173",  # ✅ PARA BUILD DE PRODUCCIÓN
        "http://127.0.0.1:4173",  # ✅ PARA BUILD DE PRODUCCIÓN
    ], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --------------------------------------------------------------------------
# 8. Endpoints de la API
# --------------------------------------------------------------------------
@app.get("/", tags=["Root"])
def read_root():
    return {"status": "Servidor FastAPI conectado y con autenticación"}

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
    return UserPublic(**created_user_from_db) # type: ignore

@app.put("/api/users/{user_id}", response_model=UserPublic, tags=["Usuarios"])
async def update_user(user_id: str, user_update: UserUpdate, admin_user: dict = Depends(get_current_admin_user)):
    if not ObjectId.is_valid(user_id): raise HTTPException(status_code=400, detail="El ID de usuario no es válido")
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_data: raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    
    result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    if result.matched_count == 0: raise HTTPException(status_code=404, detail="No se encontró el usuario")
    
    updated_user_from_db = await users_collection.find_one({"_id": ObjectId(user_id)})
    return UserPublic(**updated_user_from_db) # type: ignore

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Usuarios"])
async def delete_user(user_id: str, admin_user: dict = Depends(get_current_admin_user)):
    if not ObjectId.is_valid(user_id): raise HTTPException(status_code=400, detail="El ID de usuario no es válido")
    if str(admin_user["_id"]) == user_id: raise HTTPException(status_code=403, detail="Un administrador no puede eliminarse a sí mismo")
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0: raise HTTPException(status_code=404, detail="No se encontró el usuario a eliminar")
    return

@app.get("/api/users/me", response_model=UserPublic, tags=["Usuarios"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtiene información del usuario actual"""
    return UserPublic(**current_user)

@app.get("/api/metrics/latest", tags=["Datos de Sensores"])
async def get_latest_metrics(current_user: dict = Depends(get_current_user)):
    latest_reading = await sensor_collection.find_one({}, sort=[("ReadTime", -1)])
    if not latest_reading: raise HTTPException(status_code=404, detail="No se encontraron lecturas de sensores")
    
    return {
        "temperatura_agua": {
            "value": round(latest_reading.get("Temperature", 0), 1), 
            "unit": "°C", 
            "changeText": "Temperatura del agua",
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
    sensor_type: str,
    hours: int = 24,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene datos históricos para gráficos individuales"""
    try:
        # Calcular rango de fechas
        end_time = datetime.now(timezone.utc)
        if hours > 0:
            start_time = end_time - timedelta(hours=hours)
            query = {"ReadTime": {"$gte": start_time, "$lte": end_time}}
        else:
            query = {}  # Todo el historial
        
        # Buscar datos
        cursor = sensor_collection.find(query).sort("ReadTime", 1).limit(1000)
        readings = await cursor.to_list(length=1000)
        
        if not readings:
            return {"labels": [], sensor_type: []}
        
        # Generar etiquetas de tiempo
        labels = []
        for reading in readings:
            read_time = reading["ReadTime"]
            if hours <= 24:
                labels.append(read_time.strftime("%H:%M"))
            elif hours <= 168:  # 7 días
                labels.append(read_time.strftime("%d/%m %H:%M"))
            else:
                labels.append(read_time.strftime("%d/%m/%Y"))
        
        # Mapear datos según el tipo de sensor
        data_map = {
            "temperatura": [r.get("Temperature", 0) for r in readings],
            "ph": [r.get("pH_Value", 7.0) for r in readings],
            "conductividad": [r.get("EC", 0) for r in readings],
            "nivel": [r.get("Water_Level", 0) for r in readings]
        }
        
        return {
            "labels": labels,
            sensor_type: data_map.get(sensor_type, [])
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos históricos: {str(e)}")

@app.get("/api/sensors/individual", tags=["Datos de Sensores"])
async def get_individual_sensors_status(current_user: dict = Depends(get_current_user)):
    """Estado detallado de cada sensor individual"""
    
    try:
        current_time = datetime.now(timezone.utc)
        sensors = []
        
        # Si no hay sensores en memoria, buscar en la base de datos
        if not sensor_last_seen:
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
                
                # Asegurar que ambas fechas tengan zona horaria
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
                
                sensor_data = {
                    "uid": reservoir_id,
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
        
        # Lógica para sensores activos en memoria
        for reservoir_id, last_seen in sensor_last_seen.items():
            time_diff = (current_time - last_seen).total_seconds()
            minutes_diff = time_diff / 60
            status = sensor_status.get(reservoir_id, "unknown")
            
            # Obtener última lectura
            latest_reading = await sensor_collection.find_one(
                {"reservoirId": reservoir_id}, 
                sort=[("ReadTime", -1)]
            )
            
            sensor_data = {
                "uid": reservoir_id,
                "last_value": {
                    "value": round(latest_reading.get("Temperature", 0), 1) if latest_reading else 0,
                    "unit": "°C",
                    "type": "Temperatura"
                },
                "status": status,
                "location": f"Embalse {reservoir_id}",
                "last_reading": last_seen.isoformat(),
                "minutes_since_reading": int(minutes_diff)
            }
            
            sensors.append(sensor_data)
        
        return sensors
        
    except Exception as e:
        logger.error(f"Error obteniendo sensores individuales: {e}")
        return []

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
    
    query = {"timestamp": {"$gte": start_time, "$lte": end_time}}
    if reservoir_id:
        query["reservoirId"] = reservoir_id # type: ignore
    
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

# --------------------------------------------------------------------------
# 9. Eventos de Startup
# --------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Eventos que se ejecutan al iniciar la aplicación"""
    logger.info("🚀 Iniciando API para Dashboard de Embalses IoT")
    
    # Iniciar conexión IoT en un hilo separado para no bloquear la API
    threading.Thread(target=start_iot_connection, daemon=True).start()
    
    # Iniciar monitoreo de sensores en background
    asyncio.create_task(check_sensor_timeouts())
    logger.info("⏰ Sistema de monitoreo de sensores iniciado")