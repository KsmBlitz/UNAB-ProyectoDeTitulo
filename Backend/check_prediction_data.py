"""
Script para verificar datos disponibles para predicción
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import sensor_collection


async def check_data():
    """Verificar datos disponibles"""
    print("🔍 Verificando datos históricos...\n")
    
    # Últimos 7 días
    lookback_time = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Contar datos de pH
    ph_count = await sensor_collection.count_documents({
        "ReadTime": {"$gte": lookback_time},
        "pH": {"$exists": True, "$ne": None}
    })
    
    # Contar datos de conductividad
    ec_count = await sensor_collection.count_documents({
        "ReadTime": {"$gte": lookback_time},
        "Conductividad_Electrica": {"$exists": True, "$ne": None}
    })
    
    # Total de documentos
    total_count = await sensor_collection.count_documents({
        "ReadTime": {"$gte": lookback_time}
    })
    
    print(f"📊 Últimos 7 días:")
    print(f"   Total de registros: {total_count}")
    print(f"   Registros con pH: {ph_count}")
    print(f"   Registros con Conductividad: {ec_count}")
    print()
    
    # Mínimo requerido
    min_required = 2
    print(f"✅ Mínimo requerido para predicción: {min_required} registros")
    print()
    
    if ph_count >= min_required:
        print("✅ pH: Suficientes datos para predicción")
    else:
        print(f"❌ pH: Insuficientes datos ({ph_count}/{min_required})")
    
    if ec_count >= min_required:
        print("✅ Conductividad: Suficientes datos para predicción")
    else:
        print(f"❌ Conductividad: Insuficientes datos ({ec_count}/{min_required})")
    
    print()
    
    # Mostrar últimos registros
    print("📝 Últimos 5 registros:")
    cursor = sensor_collection.find({
        "ReadTime": {"$gte": lookback_time}
    }).sort("ReadTime", -1).limit(5)
    
    readings = await cursor.to_list(length=5)
    
    if readings:
        for i, reading in enumerate(readings, 1):
            read_time = reading.get('ReadTime')
            ph = reading.get('pH', 'N/A')
            ec = reading.get('Conductividad_Electrica', 'N/A')
            print(f"   {i}. {read_time} - pH: {ph}, EC: {ec}")
    else:
        print("   No hay registros recientes")


if __name__ == "__main__":
    asyncio.run(check_data())
