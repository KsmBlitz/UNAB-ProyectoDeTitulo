# backend/create_test_user.py
import asyncio
import motor.motor_asyncio
from passlib.context import CryptContext

# --- CONFIGURACIÓN ---
MONGO_CONNECTION_STRING = "mongodb+srv://vjestayvaldivia_db_user:KSMblitz3605.@testcluster.fxccig4.mongodb.net/?retryWrites=true&w=majority&appName=TestCluster"
DATABASE_NAME = "SampleDatabase"

# Usuario de prueba que vamos a crear
TEST_USER_EMAIL = "operario@embalses.cl"
TEST_USER_PASSWORD = "password"

# --- LÓGICA ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

async def create_user():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
    db = client[DATABASE_NAME]
    users_collection = db.users

    # Verificar si el usuario ya existe
    existing_user = await users_collection.find_one({"email": TEST_USER_EMAIL})
    if existing_user:
        print(f"El usuario '{TEST_USER_EMAIL}' ya existe en la base de datos.")
        return

    # Hashear la contraseña y crear el documento de usuario
    hashed_password = get_password_hash(TEST_USER_PASSWORD)
    user_document = {
    "email": TEST_USER_EMAIL,
    "hashed_password": hashed_password,
    "full_name": "Usuario Operario",
    "disabled": False,
    "role": "operario" # <-- Cambia el rol aquí
}

    # Insertar el usuario en la colección 'users'
    result = await users_collection.insert_one(user_document)
    print(f"Usuario creado exitosamente con el email '{TEST_USER_EMAIL}'")
    print(f"ID del nuevo usuario: {result.inserted_id}")

    client.close()

if __name__ == "__main__":
    asyncio.run(create_user())