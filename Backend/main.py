# Backend/main.py

# 1. Imports
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
import json as _json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic_settings import BaseSettings
from typing import Annotated, Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import motor.motor_asyncio
from bson import ObjectId
import asyncio
import threading
import logging
from collections import defaultdict
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Importar core_schema y PydanticCustomError para PyObjectId
from pydantic_core import CoreSchema, PydanticCustomError, core_schema

# Importar modelos de alertas
from models.alert_models import (
    AlertThresholds, ActiveAlert, AlertHistory, AlertSummary, 
    AlertConfigUpdateRequest, DismissAlertRequest, AlertLevel, AlertType, AlertStatus,
    BLUEBERRY_CHILE_THRESHOLDS, ThresholdConfig
)
import uuid

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
    
    # Variables opcionales para SMTP (configuración de email)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    # Intervalo de polling para el loop de alertas (en minutos). Usar entero; por defecto 30.
    ALERT_CHECK_INTERVAL_MINUTES: int = 30
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
# Colecciones para sistema de alertas
alerts_collection = db.alerts
alert_history_collection = db.alert_history
alert_thresholds_collection = db.alert_thresholds
# Colección para tokens de recuperación de contraseña
reset_tokens_collection = db.reset_tokens

# Estado global para alertas
active_alerts: Dict[str, ActiveAlert] = {}
user_thresholds: Dict[str, AlertThresholds] = {}

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

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

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

def generate_reset_token():
    """Genera un token seguro de 32 caracteres para recuperación de contraseña"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

async def send_reset_email(email: str, reset_token: str):
    """Envía email de recuperación de contraseña"""
    try:
        if not all([settings.SMTP_SERVER, settings.SMTP_PORT, settings.SMTP_USERNAME, 
                   settings.SMTP_PASSWORD, settings.FROM_EMAIL]):
            logger.warning("Configuración SMTP incompleta - no se puede enviar email")
            return False

        # Crear el mensaje
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL or ""
        msg['To'] = email
        msg['Subject'] = "Recuperación de Contraseña - Sistema de Embalses IoT"

        # URL de reset (en producción sería tu dominio real)
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
        
        # Cuerpo del email en HTML
        body = f"""
        <html>
        <body>
            <h2>🔐 Recuperación de Contraseña</h2>
            <p>Hola,</p>
            <p>Recibimos una solicitud para restablecer tu contraseña en el Sistema de Embalses IoT.</p>
            
            <p><strong>Para continuar:</strong></p>
            <p>Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
            
            <p style="text-align: center; margin: 20px 0;">
                <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    🔑 Restablecer Contraseña
                </a>
            </p>
            
            <p><strong>⚠️ Importante:</strong></p>
            <ul>
                <li>Este enlace expirará en <strong>1 hora</strong> por seguridad</li>
                <li>Solo puedes usar este enlace una vez</li>
                <li>Si no solicitaste este cambio, ignora este email</li>
            </ul>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
            <p style="font-size: 0.9em; color: #666;">
                Sistema de Monitoreo de Embalses IoT para Arándanos<br>
                Este es un email automático, no responda a este mensaje.
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))

        # Conectar al servidor SMTP
        server = smtplib.SMTP(settings.SMTP_SERVER or "", settings.SMTP_PORT or 587)
        server.starttls()  # Habilitar encriptación TLS
        server.login(settings.SMTP_USERNAME or "", settings.SMTP_PASSWORD or "")
        
        # Enviar el email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email de recuperación enviado exitosamente a: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email de recuperación: {e}")
        return False


async def should_send_notification(key: str) -> bool:
    """Comprueba si la notificación puede enviarse según el throttle almacenado en la colección `notifications_sent`."""
    try:
        col = db.notifications_sent
        rec = await col.find_one({"_id": key})
        if not rec:
            return True
        last_sent = rec.get("last_sent")
        if not last_sent:
            return True
        if isinstance(last_sent, str):
            try:
                last_dt = datetime.fromisoformat(last_sent)
            except Exception:
                return True
        elif isinstance(last_sent, datetime):
            last_dt = last_sent
        else:
            return True

        minutes = getattr(settings, "ALERT_EMAIL_THROTTLE_MINUTES", 60) or 60
        return (datetime.now(timezone.utc) - last_dt) > timedelta(minutes=minutes)
    except Exception as e:
        logger.error(f"Error comprobando throttle de notificación: {e}")
        return True


async def mark_notification_sent(key: str):
    """Marca la notificación enviada (upsert en notifications_sent)."""
    try:
        col = db.notifications_sent
        await col.update_one({"_id": key}, {"$set": {"last_sent": datetime.now(timezone.utc)}}, upsert=True)
    except Exception as e:
        logger.error(f"Error marcando notificación enviada: {e}")


async def clear_notifications_sent_for_alert(alert_type: str, sensor_id: Optional[str] = None):
    """Elimina registros de throttling para una alerta cuando se resuelve (para todos los usuarios).

    Borra todas las entradas cuyo _id empiece con 'alert_type:sensor_id:'
    """
    try:
        col = db.notifications_sent
        if sensor_id:
            pattern = f"^{re.escape(str(alert_type))}:{re.escape(str(sensor_id))}:"
        else:
            pattern = f"^{re.escape(str(alert_type))}:"
        await col.delete_many({"_id": {"$regex": pattern}})
        logger.info(f"Throttle cleared for alert {alert_type} sensor {sensor_id}")
    except Exception as e:
        logger.error(f"Error limpiando notifications_sent para alerta {alert_type}/{sensor_id}: {e}")


async def send_critical_alert_email(to_email: str, reservoir_name: str, alert_type: str, value: str) -> bool:
    """Envía un email HTML informando de una alerta crítica."""
    try:
        if not all([settings.SMTP_SERVER, settings.SMTP_PORT, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, settings.FROM_EMAIL]):
            logger.warning("Configuración SMTP incompleta - no se puede enviar email de alerta crítica")
            return False

        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL or ""
        msg['To'] = to_email
        msg['Subject'] = f"[ALERTA CRÍTICA] {reservoir_name} - {alert_type}"

        body = f"""
        <html>
        <body>
            <h2>🚨 Alerta Crítica</h2>
            <p><strong>Embalse:</strong> {reservoir_name}</p>
            <p><strong>Tipo de alerta:</strong> {alert_type}</p>
            <p><strong>Valor detectado:</strong> {value}</p>
            <hr>
            <p>Revisa el dashboard para más detalles.</p>
            <p style="font-size:0.9em;color:#666;">Este es un correo automático.</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(settings.SMTP_SERVER or "", settings.SMTP_PORT or 587)
        server.starttls()
        server.login(settings.SMTP_USERNAME or "", settings.SMTP_PASSWORD or "")
        server.send_message(msg)
        server.quit()

        logger.info(f"Email de alerta crítica enviado a {to_email} para {reservoir_name}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email de alerta crítica a {to_email}: {e}")
        return False

# --------------------------------------------------------------------------
# 7. Inicialización de la App FastAPI
# --------------------------------------------------------------------------
app = FastAPI(title="API para Dashboard de Embalses IoT", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],            # usar regex en lugar de lista
    allow_origin_regex=".*",     # acepta cualquier origen (devolverá Origin específico)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.post("/api/auth/forgot-password", tags=["Autenticación"])
async def forgot_password(request: ForgotPasswordRequest):
    """Inicia el proceso de recuperación de contraseña"""
    try:
        # Verificar si el usuario existe
        user = await users_collection.find_one({"email": request.email})
        if not user:
            # Por seguridad, siempre devolver éxito aunque el email no exista
            return {"message": "Si el email existe, recibirás un enlace de recuperación"}
        
        # Generar token seguro
        reset_token = generate_reset_token()
        
        # Guardar token en la base de datos con expiración de 1 hora
        token_data = {
            "email": request.email,
            "token": reset_token,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "used": False
        }
        
        await reset_tokens_collection.insert_one(token_data)
        
        # Enviar email de recuperación
        email_sent = await send_reset_email(request.email, reset_token)
        
        if email_sent:
            logger.info(f"Email de recuperación enviado exitosamente a: {request.email}")
        else:
            # Fallback: mostrar token en logs si el email falla
            logger.warning(f"Email falló - Token de recuperación para {request.email}: {reset_token}")
        
        return {"message": "Si el email existe, recibirás un enlace de recuperación"}
    
    except Exception as e:
        logger.error(f"Error en forgot_password: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/api/auth/reset-password", tags=["Autenticación"])
async def reset_password(request: ResetPasswordRequest):
    """Completa el proceso de recuperación de contraseña"""
    try:
        # Buscar token válido
        token_data = await reset_tokens_collection.find_one({
            "token": request.token,
            "used": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Token inválido o expirado")
        
        # Actualizar contraseña del usuario
        hashed_password = get_password_hash(request.new_password)
        
        result = await users_collection.update_one(
            {"email": token_data["email"]},
            {"$set": {"hashed_password": hashed_password}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Marcar token como usado
        await reset_tokens_collection.update_one(
            {"token": request.token},
            {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}}
        )
        
        logger.info(f"Contraseña actualizada para usuario: {token_data['email']}")
        
        return {"message": "Contraseña actualizada exitosamente"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en reset_password: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/api/auth/validate-reset-token/{token}", tags=["Autenticación"])
async def validate_reset_token(token: str):
    """Valida si un token de reset es válido y devuelve información"""
    try:
        # Buscar token válido
        token_data = await reset_tokens_collection.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not token_data:
            raise HTTPException(status_code=404, detail="Token inválido o expirado")
        
        # Calcular tiempo restante en minutos
        expires_at = token_data["expires_at"]
        now = datetime.now(timezone.utc)
        
        # Asegurar que expires_at tenga timezone si no lo tiene
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        time_remaining = expires_at - now
        minutes_remaining = int(time_remaining.total_seconds() / 60)
        
        return {
            "valid": True,
            "email": token_data["email"],
            "expires_in_minutes": max(0, minutes_remaining),
            "expires_at": expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating reset token: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

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

def evaluate_metric_status(value: float, threshold_config: ThresholdConfig) -> str:
    """
    Evalúa el estado de una métrica basándose en los umbrales configurados.
    Retorna: 'normal', 'warning', o 'critical'
    """
    # Valores críticos (fuera de los límites críticos)
    if (threshold_config.critical_min is not None and value < threshold_config.critical_min) or \
       (threshold_config.critical_max is not None and value > threshold_config.critical_max):
        return "critical"
    
    # Valores óptimos (dentro del rango óptimo)
    if (threshold_config.optimal_min is not None and threshold_config.optimal_max is not None and
        threshold_config.optimal_min <= value <= threshold_config.optimal_max):
        return "normal"
    
    # Valores de advertencia (fuera del rango óptimo pero dentro del rango de advertencia)
    if (threshold_config.warning_min is not None and threshold_config.warning_max is not None and
        threshold_config.warning_min <= value <= threshold_config.warning_max):
        return "warning"
    
    # Por defecto, si no está en ningún rango definido
    return "warning"

@app.get("/api/metrics/latest", tags=["Datos de Sensores"])
async def get_latest_metrics(current_user: dict = Depends(get_current_user)):
    latest_reading = await sensor_collection.find_one({}, sort=[("ReadTime", -1)])
    if not latest_reading: raise HTTPException(status_code=404, detail="No se encontraron lecturas de sensores")
    
    # Usar los umbrales para arándanos chilenos
    thresholds = BLUEBERRY_CHILE_THRESHOLDS
    
    # Obtener valores y evaluar estados
    temperatura = round(latest_reading.get("Temperature", 0), 1)
    ph = round(latest_reading.get("pH_Value", 7.0), 1)
    conductividad = round(latest_reading.get("EC", 0), 2)
    nivel_agua = round(latest_reading.get("Water_Level", 0), 1)
    
    return {
        "temperatura_agua": {
            "value": temperatura, 
            "unit": "°C", 
            "changeText": "Temperatura del agua",
            "isPositive": True,
            "status": evaluate_metric_status(temperatura, thresholds.temperature)
        },
        "ph": {
            "value": ph, 
            "unit": "", 
            "changeText": "Nivel de acidez", 
            "isPositive": True,
            "status": evaluate_metric_status(ph, thresholds.ph)
        },
        "conductividad": {
            "value": conductividad, 
            "unit": "dS/m", 
            "changeText": "Conductividad eléctrica", 
            "isPositive": True,
            "status": evaluate_metric_status(conductividad, thresholds.conductivity)
        },
        "nivel_agua": {
            "value": nivel_agua, 
            "unit": "m", 
            "changeText": "Nivel del embalse", 
            "isPositive": True,
            "status": evaluate_metric_status(nivel_agua, thresholds.water_level)
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
# 8. Endpoints de Alertas
# --------------------------------------------------------------------------

async def get_user_thresholds(user_email: str) -> AlertThresholds:
    """Obtiene la configuración de umbrales del usuario o devuelve los predefinidos"""
    if user_email in user_thresholds:
        return user_thresholds[user_email]
    
    # Buscar en base de datos
    threshold_doc = await alert_thresholds_collection.find_one({"user_email": user_email})
    if threshold_doc:
        thresholds = AlertThresholds(**threshold_doc["thresholds"])
        user_thresholds[user_email] = thresholds
        return thresholds
    
    # Devolver configuración predefinida para arándanos
    user_thresholds[user_email] = BLUEBERRY_CHILE_THRESHOLDS
    return BLUEBERRY_CHILE_THRESHOLDS

async def was_alert_recently_dismissed(alert_type: AlertType, sensor_id: str, hours_grace_period: int = 1) -> bool:
    """Verifica si una alerta del mismo tipo/sensor fue cerrada manualmente en las últimas X horas"""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_grace_period)
        
        # Log de depuración
        logger.info(f"🔍 Verificando período de gracia para {alert_type.value} sensor {sensor_id} desde {cutoff_time.isoformat()}")
        
        # Buscar en historial si hay alguna alerta cerrada manualmente para este tipo/sensor
        recent_dismissal = await alert_history_collection.find_one({
            "type": alert_type.value,
            "sensor_id": sensor_id,
            "resolution_type": "manual_dismiss",
            "dismissed_at": {"$gte": cutoff_time}
        })
        
        if recent_dismissal:
            logger.info(f"✅ Encontrada alerta cerrada recientemente para {alert_type.value}/{sensor_id} - aplicando período de gracia")
            return True
        else:
            # Verificar si hay algún registro en historial para debugging
            any_history = await alert_history_collection.find_one({"type": alert_type.value})
            logger.info(f"❌ No hay alerta cerrada reciente para {alert_type.value}/{sensor_id}. Hay historial del tipo: {any_history is not None}")
            return False
        
    except Exception as e:
        logger.error(f"Error verificando alertas cerradas recientemente: {e}")
        return False

async def evaluate_sensor_thresholds(user_email: str = "default") -> List[ActiveAlert]:
    """Evalúa las métricas actuales contra los umbrales configurados para arándanos"""
    current_alerts = []
    thresholds = await get_user_thresholds(user_email)
    
    try:
        # Obtener últimas lecturas
        latest_reading = await sensor_collection.find_one({}, sort=[("ReadTime", -1)])
        if not latest_reading:
            return current_alerts
        
        current_time = datetime.now(timezone.utc)
        sensor_id = latest_reading.get("SensorID", "Unknown")
        
        # Evaluar pH - Crítico para arándanos
        ph_value = latest_reading.get("pH_Value", 7.0)
        ph_alert = evaluate_ph_threshold(ph_value, thresholds.ph, current_time, sensor_id)
        if ph_alert:
            current_alerts.append(ph_alert)
        
        # Evaluar Conductividad - Crítico para calidad del agua
        ec_value = latest_reading.get("EC", 0)
        ec_alert = evaluate_conductivity_threshold(ec_value, thresholds.conductivity, current_time, sensor_id)
        if ec_alert:
            current_alerts.append(ec_alert)
        
        # Evaluar Temperatura
        temp_value = latest_reading.get("Temperature", 20)
        temp_alert = evaluate_temperature_threshold(temp_value, thresholds.temperature, current_time, sensor_id)
        if temp_alert:
            current_alerts.append(temp_alert)
        
        # Evaluar sensores desconectados
        sensor_alerts = await evaluate_sensor_disconnection(thresholds, current_time)
        current_alerts.extend(sensor_alerts)

        
        return current_alerts
        
    except Exception as e:
        logger.error(f"Error evaluando umbrales: {e}")
        return []

def evaluate_ph_threshold(value: float, threshold, timestamp: datetime, sensor_id: str) -> Optional[ActiveAlert]:
    """Evalúa alerta de pH específica para arándanos en Chile"""
    if value < threshold.critical_min or value > threshold.critical_max:
        return ActiveAlert(
            type=AlertType.PH_RANGE,
            level=AlertLevel.CRITICAL,
            title="pH Crítico para Arándanos",
            message=f"pH del agua ({value:.1f}) está fuera del rango crítico para arándanos",
            value=value,
            threshold_info=f"Rango óptimo para arándanos: {threshold.optimal_min}-{threshold.optimal_max}",
            location="Sistema de Riego",
            sensor_id=sensor_id,
            created_at=timestamp
        )
    elif value < threshold.warning_min or value > threshold.warning_max:
        return ActiveAlert(
            type=AlertType.PH_RANGE,
            level=AlertLevel.WARNING,
            title="pH Subóptimo para Arándanos", 
            message=f"pH del agua ({value:.1f}) no está en el rango óptimo para arándanos",
            value=value,
            threshold_info=f"Rango óptimo para arándanos: {threshold.optimal_min}-{threshold.optimal_max}",
            location="Sistema de Riego",
            sensor_id=sensor_id,
            created_at=timestamp
        )
    return None

def evaluate_conductivity_threshold(value: float, threshold, timestamp: datetime, sensor_id: str) -> Optional[ActiveAlert]:
    """Evalúa conductividad eléctrica - crítica para arándanos"""
    if value > threshold.critical_max:
        return ActiveAlert(
            type=AlertType.CONDUCTIVITY,
            level=AlertLevel.CRITICAL,
            title="Conductividad Crítica",
            message=f"Conductividad eléctrica ({value:.1f} dS/m) demasiado alta para arándanos",
            value=value,
            threshold_info=f"Conductividad óptima para arándanos: < {threshold.optimal_max} dS/m",
            location="Sistema de Riego",
            sensor_id=sensor_id,
            created_at=timestamp
        )
    elif value > threshold.warning_max:
        return ActiveAlert(
            type=AlertType.CONDUCTIVITY,
            level=AlertLevel.WARNING,
            title="Conductividad Elevada",
            message=f"Conductividad eléctrica ({value:.1f} dS/m) por encima del óptimo para arándanos",
            value=value,
            threshold_info=f"Conductividad óptima para arándanos: < {threshold.optimal_max} dS/m",
            location="Sistema de Riego",
            sensor_id=sensor_id,
            created_at=timestamp
        )
    return None

def evaluate_temperature_threshold(value: float, threshold, timestamp: datetime, sensor_id: str) -> Optional[ActiveAlert]:
    """Evalúa temperatura ambiente"""
    if value < threshold.critical_min or value > threshold.critical_max:
        return ActiveAlert(
            type=AlertType.TEMPERATURE,
            level=AlertLevel.CRITICAL,
            title="Temperatura Crítica",
            message=f"Temperatura ({value:.1f}°C) en rango crítico",
            value=value,
            threshold_info=f"Rango óptimo: {threshold.optimal_min}°C - {threshold.optimal_max}°C",
            location="Campo de Cultivo",
            sensor_id=sensor_id,
            created_at=timestamp
        )
    elif value < threshold.warning_min or value > threshold.warning_max:
        return ActiveAlert(
            type=AlertType.TEMPERATURE,
            level=AlertLevel.WARNING,
            title="Temperatura Subóptima",
            message=f"Temperatura ({value:.1f}°C) fuera del rango óptimo",
            value=value,
            threshold_info=f"Rango óptimo: {threshold.optimal_min}°C - {threshold.optimal_max}°C",
            location="Campo de Cultivo",
            sensor_id=sensor_id,
            created_at=timestamp
        )
    return None

async def evaluate_sensor_disconnection(thresholds: AlertThresholds, current_time: datetime) -> List[ActiveAlert]:
    """Evalúa sensores desconectados basado en última lectura"""
    alerts = []
    
    try:
        # Asegurar que current_time sea timezone-aware desde el inicio
        if current_time.tzinfo is None:
            current_time_utc = current_time.replace(tzinfo=timezone.utc)
        else:
            current_time_utc = current_time
        
        # Obtener todos los sensores únicos y su última lectura
        pipeline = [
            {"$group": {
                "_id": "$SensorID",
                "last_reading": {"$max": "$ReadTime"}
            }}
        ]
        
        sensors = await sensor_collection.aggregate(pipeline).to_list(length=100)

        
        for sensor in sensors:
            sensor_id = sensor["_id"]
            last_reading = sensor["last_reading"]
            
            # Normalizar last_reading a datetime timezone-aware
            if isinstance(last_reading, str):
                try:
                    last_reading_dt = datetime.fromisoformat(last_reading.replace('Z', '+00:00'))
                except ValueError:
                    # Si falla el parsing, intentar otros formatos
                    try:
                        last_reading_dt = datetime.strptime(last_reading, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                    except ValueError:
                        logger.warning(f"No se pudo parsear fecha del sensor {sensor_id}: {last_reading}")
                        continue
            elif isinstance(last_reading, datetime):
                if last_reading.tzinfo is None:
                    last_reading_dt = last_reading.replace(tzinfo=timezone.utc)
                else:
                    last_reading_dt = last_reading
            else:
                logger.warning(f"Formato de fecha desconocido para sensor {sensor_id}: {type(last_reading)}")
                continue
            
            # Calcular diferencia de tiempo
            try:
                time_diff = current_time_utc - last_reading_dt
                minutes_ago = time_diff.total_seconds() / 60
                
                logger.debug(f"Sensor {sensor_id}: {minutes_ago:.1f} minutos sin datos")
            except Exception as e:
                logger.error(f"Error calculando diferencia de tiempo para sensor {sensor_id}: {e}")
                continue
            
            # Evaluar umbrales de desconexión
            if minutes_ago > thresholds.sensor_timeout_critical:
                logger.warning(f"🚨 ALERTA CRÍTICA: Sensor {sensor_id} desconectado hace {int(minutes_ago)} minutos")
                alerts.append(ActiveAlert(
                    type=AlertType.SENSOR_DISCONNECTION,
                    level=AlertLevel.CRITICAL,
                    title="Sensor Desconectado",
                    message=f"Sensor {sensor_id} sin datos hace {int(minutes_ago)} minutos ({int(minutes_ago/60)} horas)",
                    value=minutes_ago,
                    threshold_info=f"Timeout crítico: {thresholds.sensor_timeout_critical} minutos",
                    location=f"Embalse {sensor_id}",
                    sensor_id=sensor_id,
                    created_at=current_time_utc
                ))
            elif minutes_ago > thresholds.sensor_timeout_warning:
                logger.warning(f"⚠️ ALERTA ADVERTENCIA: Sensor {sensor_id} con retraso de {int(minutes_ago)} minutos")
                alerts.append(ActiveAlert(
                    type=AlertType.SENSOR_DISCONNECTION,
                    level=AlertLevel.WARNING,
                    title="Sensor con Retraso",
                    message=f"Sensor {sensor_id} sin datos hace {int(minutes_ago)} minutos",
                    value=minutes_ago,
                    threshold_info=f"Timeout advertencia: {thresholds.sensor_timeout_warning} minutos",
                    location=f"Embalse {sensor_id}",
                    sensor_id=sensor_id,
                    created_at=current_time_utc
                ))
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error evaluando sensores desconectados: {e}")
        return []

@app.get("/api/alerts/active", tags=["Alertas"])
async def get_active_alerts(current_user: dict = Depends(get_current_user)):
    """Obtiene alertas activas no resueltas desde la base de datos"""
    try:
        # Leer alertas activas desde la base de datos
        active_alerts_cursor = alerts_collection.find({"is_resolved": False})
        active_alerts_docs = await active_alerts_cursor.to_list(length=100)
        
        # También buscar documentos sin el campo is_resolved (por compatibilidad)
        no_resolved_field_cursor = alerts_collection.find({"is_resolved": {"$exists": False}})
        no_resolved_field_docs = await no_resolved_field_cursor.to_list(length=100)
        
        # Combinar ambos resultados
        all_docs = active_alerts_docs + no_resolved_field_docs
        
        # Convertir documentos a objetos ActiveAlert
        active_alerts = []
        for doc in all_docs:
            try:
                # Asegurar que el documento tiene todos los campos requeridos
                alert = ActiveAlert(
                    id=doc.get("id", str(doc.get("_id", ""))),
                    type=AlertType(doc["type"]),
                    level=AlertLevel(doc["level"]),
                    title=doc["title"],
                    message=doc["message"],
                    value=doc.get("value"),
                    threshold_info=doc["threshold_info"],
                    location=doc["location"],
                    sensor_id=doc.get("sensor_id"),
                    created_at=doc["created_at"],
                    is_resolved=doc.get("is_resolved", False),
                    status=AlertStatus(doc.get("status", "active"))
                )
                active_alerts.append(alert)
            except Exception as e:
                logger.error(f"❌ Error procesando alerta de BD: {e} - Documento: {doc}")
                continue
        
        return {
            "alerts": active_alerts,
            "count": len(active_alerts),
            "summary": {
                "critical": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
                "warning": len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
                "info": len([a for a in active_alerts if a.level == AlertLevel.INFO]),
            },
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error obteniendo alertas activas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/api/alerts/config", tags=["Alertas"])
async def get_alert_config(current_user: dict = Depends(get_current_user)):
    """Obtiene configuración de umbrales del usuario"""
    user_email = current_user.get("email", "default")
    thresholds = await get_user_thresholds(user_email)
    return {
        "thresholds": thresholds,
        "is_default": user_email not in user_thresholds,
        "crop_type": "Arándanos (Chile)"
    }

@app.put("/api/alerts/config", tags=["Alertas"])
async def update_alert_config(
    request: AlertConfigUpdateRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Actualiza configuración de umbrales - Solo Admin"""
    user_role = current_user.get("role", "operario")
    user_email = current_user.get("email")
    
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden modificar la configuración de alertas"
        )
    
    try:
        # Actualizar en memoria
        if user_email:
            user_thresholds[user_email] = request.thresholds
        
        # Guardar en base de datos
        threshold_doc = {
            "user_email": user_email,
            "thresholds": request.thresholds.dict(),
            "updated_by": request.updated_by,
            "updated_at": datetime.now(timezone.utc),
            "reason": request.reason
        }
        
        await alert_thresholds_collection.replace_one(
            {"user_email": user_email},
            threshold_doc,
            upsert=True
        )
        
        logger.info(f"Configuración de alertas actualizada por {user_email}")
        
        return {
            "message": "Configuración de alertas actualizada exitosamente",
            "updated_at": threshold_doc["updated_at"].isoformat(),
            "thresholds": request.thresholds
        }
        
    except Exception as e:
        logger.error(f"Error actualizando configuración de alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/api/alerts/dismiss", tags=["Alertas"])
async def dismiss_alert(
    request: DismissAlertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Cierra/descarta una alerta - Operario o Admin"""
    user_email = current_user.get("email")
    user_role = current_user.get("role", "operario")
    
    try:
        # Buscar alerta activa
        alert_doc = await alerts_collection.find_one({"id": request.alert_id, "is_resolved": False})
        
        if not alert_doc:
            raise HTTPException(status_code=404, detail="Alerta no encontrada o ya resuelta")
        
        current_time = datetime.now(timezone.utc)
        
        # Marcar como resuelta
        update_result = await alerts_collection.update_one(
            {"id": request.alert_id},
            {
                "$set": {
                    "is_resolved": True,
                    "status": AlertStatus.DISMISSED,
                    "dismissed_by": user_email,
                    "dismissed_at": current_time,
                    "resolution_type": "manual_dismiss"
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se pudo cerrar la alerta")
        
        # Asegurar que created_at sea timezone-aware para el cálculo
        created_at = alert_doc["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        # Agregar al historial
        try:
            # Crear diccionario simple para historial
            history_dict = {
                "alert_id": request.alert_id,
                "type": alert_doc["type"],
                "level": alert_doc["level"], 
                "title": alert_doc["title"],
                "message": alert_doc["message"],
                "value": alert_doc.get("value"),
                "threshold_info": alert_doc["threshold_info"],
                "location": alert_doc["location"],
                "sensor_id": alert_doc.get("sensor_id"),
                "created_at": created_at,
                "dismissed_at": current_time,
                "dismissed_by": user_email,
                "dismissed_by_role": user_role,
                "resolution_type": "manual_dismiss",
                "duration_minutes": int((current_time - created_at).total_seconds() / 60)
            }
            
            insert_result = await alert_history_collection.insert_one(history_dict)
            
        except Exception as history_error:
            logger.error(f"Error insertando en historial: {history_error}")
            # No fallar el dismiss por error en historial
            pass
        
        logger.info(f"Alerta {request.alert_id} cerrada por {user_email} ({user_role})")
        
        return {
            "message": "Alerta cerrada exitosamente",
            "dismissed_at": current_time.isoformat(),
            "dismissed_by": user_email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cerrando alerta: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/api/alerts/history", tags=["Alertas"])
async def get_alert_history(
    page: int = 1,
    limit: int = 50,
    level: Optional[str] = None,
    type: Optional[str] = None,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene historial de alertas - Solo Admin"""
    user_role = current_user.get("role", "operario")
    
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden ver el historial completo de alertas"
        )
    
    try:
        # Construir filtros
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        query: Dict[str, Any] = {"created_at": {"$gte": start_time, "$lte": end_time}}
        
        if level:
            query["level"] = level
        if type:
            query["type"] = type
        
        # Contar total
        total = await alert_history_collection.count_documents(query)
        
        # Obtener página
        skip = (page - 1) * limit
        history_cursor = alert_history_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        history_raw = await history_cursor.to_list(length=limit)
        
        # Convertir datos de manera simple y robusta
        history = []
        for item in history_raw:
            try:
                # Crear diccionario limpio convertiendo tipos problemáticos
                clean_item = {}
                for key, value in item.items():
                    if isinstance(value, ObjectId):
                        clean_item[key] = str(value)
                    elif isinstance(value, datetime):
                        clean_item[key] = value.isoformat()
                    else:
                        clean_item[key] = str(value) if value is not None else None
                history.append(clean_item)
            except Exception as e:
                logger.warning(f"Error procesando item del historial: {e}")
                continue
        
        return {
            "history": history,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            },
            "filters": {
                "level": level,
                "type": type,
                "days": days
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Construir filtros
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        query: Dict[str, Any] = {"created_at": {"$gte": start_time, "$lte": end_time}}
        
        if level:
            query["level"] = level
        if type:
            query["type"] = type
        
        # Contar total
        total = await alert_history_collection.count_documents(query)
        
        # Obtener página
        skip = (page - 1) * limit
        history_cursor = alert_history_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        history_raw = await history_cursor.to_list(length=limit)
        logger.info(f"DEBUG_HISTORY: history_raw length={len(history_raw)} sample_types={[type(x) for x in (history_raw[:3] or [])]}")
        if len(history_raw) > 0:
            # Log keys and sample values types for first item
            sample = history_raw[0]
            try:
                logger.info(f"DEBUG_HISTORY: sample keys={list(sample.keys())}")
                for k in list(sample.keys())[:10]:
                    try:
                        logger.info(f"DEBUG_HISTORY: sample[{k}] type={type(sample[k])} value_preview={str(sample[k])[:120]}")
                    except Exception:
                        logger.info(f"DEBUG_HISTORY: sample[{k}] type={type(sample.get(k))} (preview failed)")
            except Exception:
                logger.info("DEBUG_HISTORY: could not introspect sample item")
        
        # Sanear recursivamente la respuesta para que sea JSON-serializable
        # - ObjectId -> str
        # - datetime -> ISO string
        # - dict/list -> recorrer recursivamente
        from datetime import datetime as _dt

        def sanitize_value(v):
            # ObjectId -> str
            if isinstance(v, ObjectId):
                return str(v)
            # datetime -> ISO
            if isinstance(v, _dt):
                try:
                    return v.isoformat()
                except Exception:
                    return str(v)
            # dict -> sanitize entries
            if isinstance(v, dict):
                return {k: sanitize_value(val) for k, val in v.items()}
            # list/tuple -> sanitize each
            if isinstance(v, list):
                return [sanitize_value(x) for x in v]
            if isinstance(v, tuple):
                return tuple(sanitize_value(x) for x in v)
            # Fallback: return as-is (enums y strings se mantienen)
            return v

        try:
            history = [sanitize_value(item) for item in history_raw]
        except Exception as e:
            logger.error(f"Error sanitizing history_raw: {e}")
            # Fallback: convert only top-level ObjectId/datetime if possible
            history = []
            for item in history_raw:
                try:
                    sanitized = {}
                    for k, v in item.items():
                        if isinstance(v, ObjectId):
                            sanitized[k] = str(v)
                        elif isinstance(v, _dt):
                            sanitized[k] = v.isoformat()
                        else:
                            sanitized[k] = v
                    history.append(sanitized)
                except Exception as e2:
                    logger.error(f"Fallback sanitize failed for item: {e2}")
                    history.append({"_raw": str(item)})
        
        response_payload = {
            "history": history,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            },
            "filters": {
                "level": level,
                "type": type,
                "days": days
            }
        }

        # Serializar manualmente usando json.dumps con un manejador por defecto
        def _default_serializer(o):
            # ObjectId -> str
            if isinstance(o, ObjectId):
                return str(o)
            # datetime -> ISO
            if isinstance(o, _dt):
                try:
                    return o.isoformat()
                except Exception:
                    return str(o)
            # Enums
            try:
                from enum import Enum as _Enum
                if isinstance(o, _Enum):
                    return o.value
            except Exception:
                pass
            # Fallback
            return str(o)

        try:
            json_text = _json.dumps(response_payload, default=_default_serializer, ensure_ascii=False)
            return PlainTextResponse(content=json_text, media_type="application/json")
        except Exception as e:
            logger.error(f"Error serializing response_payload: {e}")
            # As ultimate fallback, return empty list
            return PlainTextResponse(content=_json.dumps({"history": []}), media_type="application/json")
        
    except Exception as e:
        logger.error(f"Error obteniendo historial de alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/api/alerts/test-history", tags=["Alertas"])
async def test_alert_history(current_user: dict = Depends(get_current_user)):
    """Endpoint para probar inserción y lectura del historial"""
    try:
        # 1. Contar registros actuales
        count_before = await alert_history_collection.count_documents({})
        
        # 2. Insertar un registro de prueba
        test_record = {
            "alert_id": "test-123",
            "type": "test",
            "level": "info", 
            "title": "Prueba de historial",
            "message": "Registro de prueba",
            "created_at": datetime.now(timezone.utc),
            "dismissed_at": datetime.now(timezone.utc),
            "dismissed_by": current_user.get("email"),
            "resolution_type": "test"
        }
        
        insert_result = await alert_history_collection.insert_one(test_record)
        
        # 3. Contar después de insertar
        count_after = await alert_history_collection.count_documents({})
        
        # 4. Leer una muestra
        sample = await alert_history_collection.find({}).limit(3).to_list(3)
        
        return {
            "count_before": count_before,
            "count_after": count_after,
            "insert_id": str(insert_result.inserted_id),
            "sample_count": len(sample),
            "sample_titles": [s.get("title", "sin título") for s in sample]
        }
        
    except Exception as e:
        return {"error": str(e), "count_before": 0}

@app.get("/api/alerts/check-history", tags=["Alertas"])
async def check_history_simple():
    """Endpoint simple para verificar historial - sin autenticación"""
    try:
        count = await alert_history_collection.count_documents({})
        return {"history_count": count, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "history_count": 0}

@app.get("/api/alerts/summary", tags=["Alertas"])
async def get_alert_summary(current_user: dict = Depends(get_current_user)):
    """Obtiene resumen rápido de alertas desde la base de datos"""
    try:
        # Contar alertas activas por nivel desde la base de datos
        critical_count = await alerts_collection.count_documents({"is_resolved": False, "level": "critical"})
        warning_count = await alerts_collection.count_documents({"is_resolved": False, "level": "warning"})
        info_count = await alerts_collection.count_documents({"is_resolved": False, "level": "info"})
        
        # También contar sin el campo is_resolved por compatibilidad
        critical_no_field = await alerts_collection.count_documents({"is_resolved": {"$exists": False}, "level": "critical"})
        warning_no_field = await alerts_collection.count_documents({"is_resolved": {"$exists": False}, "level": "warning"})
        info_no_field = await alerts_collection.count_documents({"is_resolved": {"$exists": False}, "level": "info"})
        
        # Usar las cuentas más altas (incluir las que no tienen is_resolved)
        total_critical = critical_count + critical_no_field
        total_warning = warning_count + warning_no_field
        total_info = info_count + info_no_field
        
        total = total_critical + total_warning + total_info
        
        return {
            "total": total,
            "critical": total_critical,
            "warning": total_warning,
            "info": total_info,
            "has_critical": total_critical > 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error obteniendo resumen de alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.delete("/api/alerts/history/clear", tags=["Alertas"])
async def clear_alert_history(current_user: dict = Depends(get_current_user)):
    """Borra todo el historial de alertas - Solo Admin"""
    user_role = current_user.get("role", "operario")
    user_email = current_user.get("email", "unknown")
    
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden borrar el historial de alertas"
        )
    
    try:
        # Contar registros antes de borrar
        count_before = await alert_history_collection.count_documents({})
        
        # Borrar todos los registros del historial
        delete_result = await alert_history_collection.delete_many({})
        
        logger.info(f"Historial de alertas borrado por {user_email}: {delete_result.deleted_count} registros eliminados")
        
        return {
            "message": "Historial de alertas borrado exitosamente",
            "deleted_count": delete_result.deleted_count,
            "deleted_by": user_email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error borrando historial de alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


async def alert_monitoring_loop():
    """Loop de monitoreo de alertas cada 6 minutos"""
    # Determinar el intervalo (en minutos) desde la configuración
    interval_minutes = getattr(settings, "ALERT_CHECK_INTERVAL_MINUTES", 30) or 30
    logger.info(f"🚨 Sistema de alertas iniciado (polling cada {interval_minutes} minutos)")
    while True:
        try:
            logger.info("🚨 Verificando alertas del sistema...")
            
            # Evaluar alertas para configuración predefinida
            current_alerts = await evaluate_sensor_thresholds("default")
            
            # Guardar nuevas alertas en base de datos (aplicando período de gracia)
            for alert in current_alerts:
                if not alert.is_resolved:
                    # Verificar si ya existe una alerta activa
                    existing = await alerts_collection.find_one({
                        "type": alert.type,
                        "sensor_id": alert.sensor_id,
                        "is_resolved": False
                    })
                    
                    if not existing:
                        # **NUEVA VERIFICACIÓN**: Aplicar período de gracia antes de crear la alerta
                        recently_dismissed = await was_alert_recently_dismissed(
                            AlertType(alert.type), 
                            alert.sensor_id or "", 
                            hours_grace_period=1
                        )
                        
                        if not recently_dismissed:
                            # Generar ID único para la alerta
                            import uuid
                            alert.id = str(uuid.uuid4())
                            
                            # Insertar nueva alerta
                            alert_dict = alert.dict()
                            await alerts_collection.insert_one(alert_dict)
                            logger.info(f"Nueva alerta creada: {alert.title} - {alert.message}")

                            # Notificar por email si es crítica (respetando throttling y preferencias del usuario)
                            try:
                                level = (alert.level or "").lower()
                                if level in ("critical", "crítica", "crítico"):
                                    admins = await users_collection.find({"role": "admin", "disabled": {"$ne": True}}).to_list(1000)
                                    for admin in admins:
                                        email = admin.get("email")
                                        if not email:
                                            continue
                                        if admin.get("notifications_enabled", True) is False:
                                            continue

                                        user_id = str(admin.get("_id"))
                                        alert_key = f"{alert.type}:{alert.sensor_id}:{user_id}"

                                        try:
                                            if await should_send_notification(alert_key):
                                                sent = await send_critical_alert_email(
                                                    email,
                                                    alert.location or alert.sensor_id or "Embalse",
                                                    alert.title or alert.type,
                                                    str(alert.value or alert_dict.get("value", "N/A"))
                                                )
                                                if sent:
                                                    await mark_notification_sent(alert_key)
                                        except Exception as e:
                                            logger.error(f"Error enviando notificación a {email}: {e}")
                            except Exception as e:
                                logger.error(f"Error procesando notificaciones por email para la alerta {alert.title}: {e}")
                        else:
                            logger.info(f"🚫 Alerta bloqueada por período de gracia: {alert.title} para sensor {alert.sensor_id}")
                    else:
                        logger.debug(f"Alerta ya existe: {alert.title} para sensor {alert.sensor_id}")
            
            # Auto-resolver alertas que ya no aplican
            await auto_resolve_alerts()
            
        except Exception as e:
            logger.error(f"Error en monitoreo de alertas: {e}")
        
        # Esperar el intervalo configurado antes de la siguiente verificación
        try:
            await asyncio.sleep(int(interval_minutes) * 60)
        except Exception:
            # En caso de error inesperado con el valor, caer a 30 minutos como fallback
            await asyncio.sleep(30 * 60)

async def auto_resolve_alerts():
    """Auto-resuelve alertas cuando las condiciones mejoran"""
    try:
        # Obtener alertas activas
        active_alerts_cursor = alerts_collection.find({"is_resolved": False})
        active_alerts = await active_alerts_cursor.to_list(length=100)
        
        current_time = datetime.now(timezone.utc)
        
        for alert_doc in active_alerts:
            alert_type = alert_doc.get("type")
            sensor_id = alert_doc.get("sensor_id")
            
            # Verificar si la condición aún se mantiene
            should_resolve = await check_if_alert_should_resolve(alert_type, sensor_id)
            
            if should_resolve:
                # Marcar como auto-resuelta
                await alerts_collection.update_one(
                    {"_id": alert_doc["_id"]},
                    {
                        "$set": {
                            "is_resolved": True,
                            "status": AlertStatus.AUTO_RESOLVED,
                            "resolved_at": current_time,
                            "resolution_type": "auto_resolved"
                        }
                    }
                )
                
                # Agregar al historial
                history_entry = AlertHistory(
                    alert_id=alert_doc["id"],
                    type=AlertType(alert_doc["type"]),
                    level=AlertLevel(alert_doc["level"]),
                    title=alert_doc["title"],
                    message=alert_doc["message"],
                    value=alert_doc.get("value"),
                    threshold_info=alert_doc["threshold_info"],
                                       location=alert_doc["location"],
                    sensor_id=alert_doc.get("sensor_id"),
                    created_at=alert_doc["created_at"],
                    resolved_at=current_time,
                    resolution_type="auto_resolved",
                    duration_minutes=int((current_time - alert_doc["created_at"]).total_seconds() / 60)
                )
                
                await alert_history_collection.insert_one(history_entry.dict())
                logger.info(f"Alerta auto-resuelta: {alert_doc['title']}")
                # Limpiar registros de notificaciones enviadas para esta alerta (permitir re-notificación si se vuelve a generar)
                try:
                    await clear_notifications_sent_for_alert(alert_doc.get("type"), alert_doc.get("sensor_id"))
                except Exception as e:
                    logger.error(f"Error limpiando throttle tras resolución de alerta: {e}")
                
    except Exception as e:
        logger.error(f"Error en auto-resolución de alertas: {e}")

async def check_if_alert_should_resolve(alert_type: str, sensor_id: str) -> bool:
    """Verifica si una alerta específica debe auto-resolverse"""
    try:
        thresholds = BLUEBERRY_CHILE_THRESHOLDS
        
        if alert_type in [AlertType.PH_RANGE, AlertType.CONDUCTIVITY, AlertType.TEMPERATURE]:
            # Obtener última lectura del sensor específico o general
            query = {}
            if sensor_id and sensor_id != "Unknown":
                query["SensorID"] = sensor_id
            
            latest_reading = await sensor_collection.find_one(query, sort=[("ReadTime", -1)])
            if not latest_reading:
                return False
            
            # Verificar si los valores están ahora en rango normal
            if alert_type == AlertType.PH_RANGE:
                ph_value = latest_reading.get("pH_Value", 7.0)
                return (thresholds.ph.optimal_min <= ph_value <= thresholds.ph.optimal_max)
            
            elif alert_type == AlertType.CONDUCTIVITY:
                ec_value = latest_reading.get("EC", 0)
                return (ec_value <= thresholds.conductivity.optimal_max)
            
            elif alert_type == AlertType.TEMPERATURE:
                temp_value = latest_reading.get("Temperature", 20)
                return (thresholds.temperature.optimal_min <= temp_value <= thresholds.temperature.optimal_max)
        
        elif alert_type == AlertType.SENSOR_DISCONNECTION:
            # Verificar si el sensor ya está enviando datos nuevamente
            if sensor_id:
                latest_reading = await sensor_collection.find_one(
                    {"SensorID": sensor_id}, 
                    sort=[("ReadTime", -1)]
                )
                
                if latest_reading:
                    last_reading_time = latest_reading.get("ReadTime")
                    
                    # Normalizar last_reading_time a datetime timezone-aware
                    if isinstance(last_reading_time, str):
                        try:
                            last_reading_time_dt = datetime.fromisoformat(last_reading_time.replace('Z', '+00:00'))
                        except ValueError:
                            try:
                                last_reading_time_dt = datetime.strptime(last_reading_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                            except ValueError:
                                logger.warning(f"No se pudo parsear fecha para resolución del sensor {sensor_id}: {last_reading_time}")
                                return False
                    elif isinstance(last_reading_time, datetime):
                        if last_reading_time.tzinfo is None:
                            last_reading_time_dt = last_reading_time.replace(tzinfo=timezone.utc)
                        else:
                            last_reading_time_dt = last_reading_time
                    else:
                        logger.warning(f"Formato de fecha desconocido para resolución del sensor {sensor_id}: {type(last_reading_time)}")
                        return False
                    
                    minutes_ago = (datetime.now(timezone.utc) - last_reading_time_dt).total_seconds() / 60

                    return minutes_ago < thresholds.sensor_timeout_warning
        
        return False
        
    except Exception as e:
        logger.error(f"Error verificando resolución de alerta: {e}")
        return False

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
    
    # Iniciar sistema de alertas cada 6 minutos
    asyncio.create_task(alert_monitoring_loop())
    logger.info("🚨 Sistema de alertas iniciado (polling cada 6 minutos)")