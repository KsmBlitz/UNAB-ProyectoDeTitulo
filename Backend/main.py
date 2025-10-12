# backend/main.py

# 1. Imports
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from pydantic_settings import BaseSettings
from typing import Annotated, Optional, List
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import motor.motor_asyncio
from bson import ObjectId
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import secrets

# Importar core_schema y PydanticCustomError para PyObjectId
from pydantic_core import CoreSchema, PydanticCustomError, core_schema


# --------------------------------------------------------------------------
# 2. Configuración Centralizada (Lee desde el archivo .env)
# --------------------------------------------------------------------------
class Settings(BaseSettings):
    MONGO_CONNECTION_STRING: str
    DATABASE_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    # Nuevas configuraciones para email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

# --------------------------------------------------------------------------
# 3. Conexión a la Base de Datos
# --------------------------------------------------------------------------
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING)
db = client[settings.DATABASE_NAME]
users_collection = db.users
sensor_collection = db.Sensor_Data
password_reset_collection = db.password_reset_tokens

# --------------------------------------------------------------------------
# 4. Modelos de Datos (Pydantic) - CON LA CORRECCIÓN FINAL PARA ObjectId
# --------------------------------------------------------------------------

# Clase PyObjectId personalizada para Pydantic v2
# Esta es la implementación recomendada para manejar ObjectId en Pydantic v2
# Tomado de la documentación de Pydantic/FastAPI
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: any, handler) -> CoreSchema:
        def validate_from_str(input_value: str) -> ObjectId:
            if not ObjectId.is_valid(input_value):
                raise PydanticCustomError("object_id", "Invalid ObjectId")
            return ObjectId(input_value)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(), # Cuando se envía a JSON, es un string
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId), # Si ya es ObjectId, lo acepta
                core_schema.no_info_after_validator_function(validate_from_str, core_schema.str_schema()) # Si es string, lo valida y convierte a ObjectId
            ]),
            serialization=core_schema.to_string_ser_schema(), # Cómo serializar de ObjectId a string
        )

# Para usar este tipo personalizado en los modelos
# No necesitamos Annotated con BeforeValidator si PyObjectId ya define el schema
# Solo necesitamos importarlo de typing
from typing import Any # Asegúrate de que Any esté importado


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
    id: PyObjectId = Field(alias='_id') # Usamos el tipo PyObjectId
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True, # Permitir que PyObjectId sea un tipo arbitrario
        json_encoders={ObjectId: str} # Asegurarse de que ObjectId se convierta a str en la salida JSON
    )

class UserCreate(UserBase):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# --------------------------------------------------------------------------
# 5. Utilidades y Dependencias de Seguridad (sin cambios)
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
        email: str = payload.get("sub")
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
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --------------------------------------------------------------------------
# 7. Endpoints de la API
# --------------------------------------------------------------------------
@app.get("/", tags=["Root"])
def read_root():
    return {"status": "Servidor FastAPI conectado y con autenticación"}

@app.post("/api/token", response_model=Token, tags=["Autenticación"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos")
    access_token = create_access_token(data={"sub": user["email"], "role": user.get("role")})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users", response_model=List[UserPublic], tags=["Usuarios"])
async def read_users(admin_user: dict = Depends(get_current_admin_user)):
    users_from_db = await users_collection.find().to_list(1000) # Increased limit
    # Pydantic con PyObjectId ahora manejará la conversión de ObjectId a str automáticamente
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
    return UserPublic(**created_user_from_db)

@app.put("/api/users/{user_id}", response_model=UserPublic, tags=["Usuarios"])
async def update_user(user_id: str, user_update: UserUpdate, admin_user: dict = Depends(get_current_admin_user)):
    if not ObjectId.is_valid(user_id): raise HTTPException(status_code=400, detail="El ID de usuario no es válido")
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_data: raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    
    result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    if result.matched_count == 0: raise HTTPException(status_code=404, detail="No se encontró el usuario")
    
    updated_user_from_db = await users_collection.find_one({"_id": ObjectId(user_id)})
    return UserPublic(**updated_user_from_db)

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Usuarios"])
async def delete_user(user_id: str, admin_user: dict = Depends(get_current_admin_user)):
    if not ObjectId.is_valid(user_id): raise HTTPException(status_code=400, detail="El ID de usuario no es válido")
    if str(admin_user["_id"]) == user_id: raise HTTPException(status_code=403, detail="Un administrador no puede eliminarse a sí mismo")
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0: raise HTTPException(status_code=404, detail="No se encontró el usuario a eliminar")
    return


@app.get("/api/users/me", response_model=UserPublic, tags=["Usuarios"])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserPublic(**current_user)

@app.get("/api/metrics/latest", tags=["Datos de Sensores"])
async def get_latest_metrics(current_user: dict = Depends(get_current_user)):
    latest_reading = await sensor_collection.find_one({}, sort=[("ReadTime", -1)])
    if not latest_reading: raise HTTPException(status_code=404, detail="No se encontraron lecturas de sensores")
    return {
        "temperatura": {"value": latest_reading.get("Temperature", 0), "unit": "C°", "changeText": "Leído desde la DB", "isPositive": True},
        "ph": {"value": latest_reading.get("pH_Value", 0), "unit": "", "changeText": "Leído desde la DB", "isPositive": True},
        "nitrogeno": {"value": latest_reading.get("Nitrogen", 0), "unit": "mg/kg", "changeText": "Nivel en suelo", "isPositive": True},
        "electroconductividad": {"value": latest_reading.get("EC", 0), "unit": "dS/m", "changeText": "Conductividad", "isPositive": True},
    }

@app.get("/api/charts/water-level", tags=["Datos de Sensores"])
async def get_water_level_data(current_user: dict = Depends(get_current_user)):
    cursor = sensor_collection.find({}, sort=[("ReadTime", -1)]).limit(30)
    readings = await cursor.to_list(length=30)
    readings.reverse()
    if not readings: raise HTTPException(status_code=404, detail="No hay suficientes datos para el gráfico")
    return {
        "labels": [r["ReadTime"].strftime("%d-%b") for r in readings],
        "real_level": [r.get("Potassium", 0) for r in readings],
        "expected_level": [r.get("Potassium", 0) + 5 for r in readings]
    }

# --------------------------------------------------------------------------
# 8. Endpoints de Recuperación de Contraseña
# --------------------------------------------------------------------------
# Actualizar las importaciones y funciones de email

# Función para enviar email (actualizada)
async def send_reset_email(email: str, reset_token: str):
    """Envía email con el token de recuperación"""
    try:
        # Solo enviar email si las credenciales están configuradas
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            print(f"⚠️  Email no configurado. Token para {email}: {reset_token}")
            print(f"🔗 URL: http://localhost:5173/reset-password?token={reset_token}")
            return True
        
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.FROM_EMAIL or settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "🔐 Recuperación de Contraseña - Embalses IoT"
        
        # Crear el enlace de recuperación
        reset_url = f"http://localhost:5173/reset-password?token={reset_token}"
        
        # Cuerpo del email en texto plano
        text_body = f"""
        Hola,
        
        Has solicitado recuperar tu contraseña para el sistema Embalses IoT.
        
        Haz clic en el siguiente enlace para restablecer tu contraseña:
        {reset_url}
        
        Este enlace expirará en 1 hora por seguridad.
        
        Si no solicitaste este cambio, puedes ignorar este mensaje de forma segura.
        
        Saludos,
        Equipo Embalses IoT
        """
        
        # Cuerpo del email en HTML (más atractivo)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
                .button:hover {{ background-color: #218838; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.9em; color: #6c757d; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Recuperación de Contraseña</h1>
                    <p>Sistema Embalses IoT</p>
                </div>
                <div class="content">
                    <h2>Hola,</h2>
                    <p>Has solicitado recuperar tu contraseña para el sistema <strong>Embalses IoT</strong>.</p>
                    <p>Haz clic en el siguiente botón para restablecer tu contraseña de forma segura:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">🔄 Restablecer Contraseña</a>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Importante:</strong>
                        <ul>
                            <li>Este enlace expirará en <strong>1 hora</strong> por seguridad</li>
                            <li>Solo funciona una vez</li>
                            <li>Si no fuiste tú quien solicitó esto, ignora este mensaje</li>
                        </ul>
                    </div>
                    
                    <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; background-color: #e9ecef; padding: 10px; border-radius: 4px;">
                        {reset_url}
                    </p>
                </div>
                <div class="footer">
                    <p>Este mensaje fue enviado automáticamente. No respondas a este email.</p>
                    <p><strong>Equipo Embalses IoT</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Adjuntar ambas versiones
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Configurar y enviar
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        # Enviar email
        server.sendmail(settings.FROM_EMAIL or settings.SMTP_USERNAME, email, msg.as_string())
        server.quit()
        
        print(f"✅ Email enviado exitosamente a {email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email a {email}: {e}")
        # En caso de error, mostrar el token en consola como fallback
        print(f"🔗 Token de recuperación: {reset_token}")
        print(f"🔗 URL: http://localhost:5173/reset-password?token={reset_token}")
        return False

# Actualizar el endpoint forgot_password
@app.post("/api/auth/forgot-password", tags=["Autenticación"])
async def forgot_password(request: PasswordResetRequest):
    """Solicitar recuperación de contraseña"""
    try:
        # Verificar que el usuario existe
        user = await users_collection.find_one({"email": request.email})
        if not user:
            # Por seguridad, siempre devolvemos el mismo mensaje
            return {"message": "Si el email está registrado, recibirás las instrucciones para recuperar tu contraseña en unos minutos."}
        
        # Verificar que el usuario no esté deshabilitado
        if user.get("disabled", False):
            return {"message": "Si el email está registrado, recibirás las instrucciones para recuperar tu contraseña en unos minutos."}
        
        # Invalidar tokens anteriores para este email (seguridad extra)
        await password_reset_collection.update_many(
            {"email": request.email, "used": False},
            {"$set": {"used": True}}
        )
        
        # Generar token criptográficamente seguro
        reset_token = secrets.token_urlsafe(32)
        
        # CAMBIO CLAVE: Usar datetime sin timezone para consistencia
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = now_utc + timedelta(hours=1)
        
        # Guardar token con información adicional de seguridad
        reset_data = {
            "email": request.email,
            "token": reset_token,
            "created_at": now_utc,
            "expires_at": expires_at,
            "used": False,
            "ip_address": None,  # Podrías capturar la IP del request
            "user_agent": None,  # Podrías capturar el user agent
        }
        
        await password_reset_collection.insert_one(reset_data)
        
        # Intentar enviar email
        email_sent = await send_reset_email(request.email, reset_token)
        
        if email_sent:
            print(f"🔐 Solicitud de recuperación procesada para {request.email}")
        else:
            print(f"⚠️  Error enviando email, pero token generado para {request.email}")
        
        # Siempre devolvemos el mismo mensaje por seguridad
        return {"message": "Si el email está registrado, recibirás las instrucciones para recuperar tu contraseña en unos minutos."}
        
    except Exception as e:
        print(f"❌ Error en forgot_password: {e}")
        # En caso de cualquier error, devolvemos el mensaje genérico
        return {"message": "Si el email está registrado, recibirás las instrucciones para recuperar tu contraseña en unos minutos."}

# Actualizar el endpoint reset_password
@app.post("/api/auth/reset-password", tags=["Autenticación"])
async def reset_password(request: PasswordResetConfirm):
    """Confirmar nueva contraseña con token"""
    try:
        # Validar longitud mínima de contraseña
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="La contraseña debe tener al menos 8 caracteres"
            )
        
        # CAMBIO CLAVE: Usar datetime sin timezone para la comparación
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Buscar token válido
        reset_record = await password_reset_collection.find_one({
            "token": request.token,
            "used": False,
            "expires_at": {"$gt": now_utc}
        })
        
        if not reset_record:
            raise HTTPException(
                status_code=400,
                detail="El enlace de recuperación es inválido o ha expirado. Solicita uno nuevo."
            )
        
        # Verificar que el usuario aún existe y no está deshabilitado
        user = await users_collection.find_one({"email": reset_record["email"]})
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Usuario no encontrado"
            )
        
        if user.get("disabled", False):
            raise HTTPException(
                status_code=400,
                detail="Esta cuenta está deshabilitada"
            )
        
        # Actualizar contraseña
        hashed_password = get_password_hash(request.new_password)
        
        result = await users_collection.update_one(
            {"email": reset_record["email"]},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "password_changed_at": now_utc
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Error actualizando la contraseña")
        
        # Marcar token como usado y agregar timestamp
        await password_reset_collection.update_one(
            {"token": request.token},
            {
                "$set": {
                    "used": True,
                    "used_at": now_utc
                }
            }
        )
        
        # Invalidar todos los demás tokens pendientes para este usuario
        await password_reset_collection.update_many(
            {
                "email": reset_record["email"],
                "used": False,
                "token": {"$ne": request.token}
            },
            {"$set": {"used": True}}
        )
        
        print(f"✅ Contraseña actualizada exitosamente para {reset_record['email']}")
        
        return {"message": "✅ Contraseña actualizada exitosamente. Ya puedes iniciar sesión con tu nueva contraseña."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en reset_password: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

# ACTUALIZAR el endpoint de validación - ESTE ES EL MÁS IMPORTANTE
@app.get("/api/auth/validate-reset-token/{token}", tags=["Autenticación"])
async def validate_reset_token(token: str):
    """Validar si un token de reset es válido"""
    try:
        # CAMBIO CLAVE: Usar datetime sin timezone para la comparación
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Buscar el token
        reset_record = await password_reset_collection.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": now_utc}
        })
        
        if not reset_record:
            raise HTTPException(
                status_code=400, 
                detail="El enlace de recuperación es inválido o ha expirado"
            )
        
        # Verificar que el usuario aún existe
        user = await users_collection.find_one({"email": reset_record["email"]})
        if not user or user.get("disabled", False):
            raise HTTPException(
                status_code=400, 
                detail="El enlace de recuperación ya no es válido"
            )
        
        # Calcular tiempo restante - MANEJAR POSIBLES DIFERENCIAS DE TIMEZONE
        expires_at = reset_record["expires_at"]
        
        # Si expires_at tiene timezone info, quitársela
        if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        
        time_remaining = expires_at - now_utc
        minutes_remaining = max(0, int(time_remaining.total_seconds() / 60))
        
        return {
            "valid": True,
            "email": reset_record["email"],
            "expires_in_minutes": minutes_remaining
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error validando token: {e}")
        raise HTTPException(
            status_code=400, 
            detail="Error validando el enlace de recuperación"
        )
