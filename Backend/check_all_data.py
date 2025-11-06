"""
Script para verificar TODOS los datos en la base de datos
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import sensor_collection


async def check_all_data():
    """Verificar todos los datos"""
    print("🔍 Verificando TODOS los datos en la base de datos...\n")
    
    # Total de documentos
    total_count = await sensor_collection.count_documents({})
    
    print(f"📊 Total de registros en la base de datos: {total_count}\n")
    
    if total_count > 0:
        # Mostrar los 10 registros más recientes
        print("📝 Los 10 registros más recientes:")
        cursor = sensor_collection.find({}).sort("ReadTime", -1).limit(10)
        
        readings = await cursor.to_list(length=10)
        
        for i, reading in enumerate(readings, 1):
            read_time = reading.get('ReadTime', 'N/A')
            ph = reading.get('pH', 'N/A')
            ec = reading.get('Conductividad_Electrica', 'N/A')
            sensor_id = reading.get('SensorID', reading.get('sensor_id', 'N/A'))
            print(f"   {i}. {read_time} - Sensor: {sensor_id}, pH: {ph}, EC: {ec}")
    else:
        print("❌ No hay datos en la base de datos")
        print("\n💡 Para que el modelo de predicción funcione, necesitas:")
        print("   1. Que el ESP32 esté enviando datos")
        print("   2. O insertar datos de prueba manualmente")


if __name__ == "__main__":
    asyncio.run(check_all_data())
