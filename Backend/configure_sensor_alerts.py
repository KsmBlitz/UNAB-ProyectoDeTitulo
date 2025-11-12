#!/usr/bin/env python3
"""
Script para configurar alertas automáticas en sensores cuando llegan datos
Configuración optimizada para arándanos
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

MONGODB_URI = os.getenv('MONGO_CONNECTION_STRING')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'SampleDatabase')

# Configuración por defecto para arándanos
DEFAULT_ALERT_CONFIG = {
    "enabled": True,
    "parameters": {
        "ph": {
            "min": 4.5, 
            "max": 5.5,
            "critical_min": 4.0,
            "critical_max": 6.0
        },
        "temperature": {
            "min": 15, 
            "max": 25,
            "critical_min": 10,
            "critical_max": 30
        },
        "ec": {
            "min": 0.0, 
            "max": 2.0,
            "critical_min": 0.0,
            "critical_max": 3.0
        },
        "water_level": {
            "min": 20.0,
            "max": 100.0,
            "critical_min": 10.0,
            "critical_max": 100.0
        }
    },
    "notification_enabled": True,
    "whatsapp_enabled": True,
    "email_enabled": True
}

print("=" * 80)
print("⚙️  CONFIGURACIÓN AUTOMÁTICA DE ALERTAS")
print("=" * 80)
print()


async def main():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    sensors_collection = db["sensors"]
    sensor_data_collection = db["Sensor_Data"]  # Nombre correcto de la colección
    
    try:
        print("📡 Verificando sensores en el sistema...")
        print()
        
        # Buscar sensores en Sensor_Data (campo SensorID)
        sensor_ids = await sensor_data_collection.distinct("SensorID")
        
        if not sensor_ids:
            print("⚠️  No hay datos de sensores todavía")
            print()
            print("ℹ️  Las alertas se configurarán automáticamente cuando:")
            print("   1. Los sensores ESP32 envíen datos")
            print("   2. El backend procese los datos")
            print("   3. Este script detecte nuevos sensores")
            print()
            return
        
        print(f"✓ Encontrados {len(sensor_ids)} sensor(es) con datos:")
        for sid in sensor_ids:
            print(f"  - {sid}")
        print()
        
        # Configurar cada sensor
        configured_count = 0
        updated_count = 0
        
        for sensor_id in sensor_ids:
            # Verificar si el sensor existe en la colección sensors
            sensor = await sensors_collection.find_one({"sensor_id": sensor_id})
            
            if not sensor:
                # Crear sensor con configuración por defecto
                print(f"📝 Creando sensor: {sensor_id}")
                
                sensor_doc = {
                    "sensor_id": sensor_id,
                    "name": f"Sensor {sensor_id}",
                    "location": "Campo de arándanos",
                    "type": "IoT_Monitoring",
                    "status": "active",
                    "alert_config": DEFAULT_ALERT_CONFIG,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await sensors_collection.insert_one(sensor_doc)
                configured_count += 1
                print(f"  ✅ Sensor creado con alertas activadas")
                
            else:
                # Actualizar configuración de alertas si no está habilitada
                current_config = sensor.get("alert_config", {})
                
                if not current_config.get("enabled"):
                    print(f"📝 Actualizando sensor: {sensor_id}")
                    
                    await sensors_collection.update_one(
                        {"sensor_id": sensor_id},
                        {
                            "$set": {
                                "alert_config": DEFAULT_ALERT_CONFIG,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    updated_count += 1
                    print(f"  ✅ Alertas activadas")
                else:
                    print(f"✓ {sensor_id}: Ya tiene alertas configuradas")
        
        print()
        print("=" * 80)
        print("📊 RESUMEN:")
        print("=" * 80)
        print(f"Sensores nuevos configurados: {configured_count}")
        print(f"Sensores actualizados: {updated_count}")
        print(f"Sensores sin cambios: {len(sensor_ids) - configured_count - updated_count}")
        print()
        
        if configured_count > 0 or updated_count > 0:
            print("✅ ¡CONFIGURACIÓN COMPLETADA!")
            print()
            print("📋 Configuración aplicada (Arándanos):")
            print("  • pH: 4.5-5.5 (crítico: 4.0-6.0)")
            print("  • Temperatura: 15-25°C (crítico: 10-30°C)")
            print("  • EC: 0-2 dS/m (crítico: 0-3 dS/m)")
            print("  • Water Level: 20-100% (crítico: 10-100%)")
            print()
            print("🔔 Notificaciones activadas:")
            print("  • WhatsApp: ✅")
            print("  • Email: ✅")
            print()
            print("⚡ Las alertas se generarán automáticamente cuando:")
            print("  1. Lleguen nuevos datos del ESP32")
            print("  2. Los valores estén fuera del rango configurado")
            print("  3. El alert_watcher detectará y enviará notificaciones")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
