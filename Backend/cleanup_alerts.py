"""
Script para limpiar alertas incompatibles de la base de datos
"""
import asyncio
import sys
from app.config.database import get_database

async def cleanup_alerts():
    """Remove old alerts with incompatible schemas"""
    db = await get_database()
    alerts_collection = db["alerts"]
    
    print("=== LIMPIEZA DE ALERTAS INCOMPATIBLES ===\n")
    
    # Find problematic alerts
    problematic = await alerts_collection.find({
        "$or": [
            {"source": None},
            {"type": "conductivity"},
            {"type": "ph_range"}
        ]
    }).to_list(length=100)
    
    print(f"Alertas problemáticas encontradas: {len(problematic)}\n")
    
    if problematic:
        for alert in problematic:
            print(f"- ID: {alert.get('_id')}")
            print(f"  Tipo: {alert.get('type')}")
            print(f"  Source: {alert.get('source')}")
            print(f"  Created: {alert.get('created_at')}")
            print()
        
        # Delete them
        result = await alerts_collection.delete_many({
            "$or": [
                {"source": None},
                {"type": "conductivity"},
                {"type": "ph_range"}
            ]
        })
        
        print(f"✓ {result.deleted_count} alertas eliminadas\n")
    else:
        print("No se encontraron alertas problemáticas\n")
    
    # Show remaining alerts
    remaining = await alerts_collection.count_documents({})
    print(f"Alertas restantes: {remaining}")
    
    if remaining > 0:
        alerts = await alerts_collection.find({}).to_list(length=10)
        print("\nAlertas actuales:")
        for alert in alerts:
            print(f"- Tipo: {alert.get('type')}, Source: {alert.get('source')}")

if __name__ == "__main__":
    asyncio.run(cleanup_alerts())
