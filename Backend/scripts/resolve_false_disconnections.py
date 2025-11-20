#!/usr/bin/env python3
"""
Resolve false sensor_disconnection alerts by checking if sensor has recent data.
Runs inside backend container (uses app services).
"""
import asyncio
import os
import sys
import json
from datetime import datetime, timezone

# Ensure project package imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.config.database import db
    from app.repositories.alert_repository import alert_repository
    from app.services.sensor_service import sensor_service
except Exception as e:
    print(json.dumps({"error": f"Failed to import app modules: {e}"}))
    raise

async def main():
    alerts_coll = db['alerts']
    # Find active sensor_disconnection alerts
    cursor = alerts_coll.find({'type': 'sensor_disconnection', 'is_resolved': False})
    alerts = await cursor.to_list(length=None)
    results = []
    for a in alerts:
        sensor_id = a.get('sensor_id')
        alert_id = str(a.get('_id'))
        try:
            connected = await sensor_service.is_sensor_connected(sensor_id)
        except Exception as e:
            results.append({'alert_id': alert_id, 'sensor_id': sensor_id, 'error': str(e)})
            continue
        if connected:
            # Dismiss using repository so history move happens consistently
            try:
                await alert_repository.dismiss_alert(alert_id, 'system-auto', reason='False disconnection - reading present')
                results.append({'alert_id': alert_id, 'sensor_id': sensor_id, 'action': 'dismissed'})
            except Exception as e:
                results.append({'alert_id': alert_id, 'sensor_id': sensor_id, 'error': str(e)})
        else:
            results.append({'alert_id': alert_id, 'sensor_id': sensor_id, 'action': 'left_open'})

    print(json.dumps({'checked': len(alerts), 'results': results}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
