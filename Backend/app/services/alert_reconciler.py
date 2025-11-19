"""
Alert Reconciler Service

Background task that periodically scans active measurement alerts and auto-dismisses
those whose sensors are currently disconnected. This acts as a safety net against
direct DB inserts or race conditions that allow transient false-positive alerts.

The reconciler records an audit entry in `alert_audit` for each auto-dismiss action.
"""
import asyncio
import logging
from datetime import datetime
from typing import List

from app.config.database import db
from app.services.sensor_service import sensor_service
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)

MEASUREMENT_TYPES: List[str] = ['ph', 'ph_range', 'temperature', 'ec', 'water_level', 'conductivity']


async def start_reconciler(interval_seconds: int = 60):
    """Start the reconciler loop. Runs until application shutdown."""
    alerts_coll = db.get_collection('alerts')
    audit_coll = db.get_collection('alert_audit')
    logger.info(f"Alert reconciler started (interval={interval_seconds}s)")

    while True:
        try:
            # Find active measurement alerts
            cursor = alerts_coll.find({
                'is_resolved': False,
                'type': {'$in': MEASUREMENT_TYPES}
            })
            alerts = await cursor.to_list(length=None)

            for a in alerts:
                alert_id = str(a.get('_id'))
                sensor_id = a.get('sensor_id')
                alert_type = (a.get('type') or '').lower()

                if not sensor_id:
                    # If alert lacks sensor_id, skip but record audit
                    try:
                        await audit_coll.insert_one({
                            'alert_id': alert_id,
                            'detected_at': datetime.utcnow(),
                            'sensor_id': None,
                            'alert_type': alert_type,
                            'action': 'skipped_no_sensor_id'
                        })
                    except Exception:
                        logger.exception('Failed to write audit for alert without sensor_id')
                    continue

                try:
                    is_connected = await sensor_service.is_sensor_connected(sensor_id)
                except Exception:
                    logger.exception(f'Failed to check connection for sensor {sensor_id} (alert {alert_id})')
                    continue

                if not is_connected:
                    logger.info(f"Reconciler auto-dismissing alert {alert_id} ({alert_type}) for disconnected sensor {sensor_id}")
                    # record audit before dismiss
                    try:
                        await audit_coll.insert_one({
                            'alert_id': alert_id,
                            'detected_at': datetime.utcnow(),
                            'sensor_id': sensor_id,
                            'alert_type': alert_type,
                            'full_document': a,
                            'action': 'reconciler_auto_dismiss_attempt'
                        })
                    except Exception:
                        logger.exception('Failed to write reconciler audit')

                    try:
                        await alert_service.dismiss_alert(alert_id=alert_id, user_email='system@reconciler', user_role='system', reason='Auto-reconciler: sensor disconnected')
                        try:
                            await audit_coll.update_one({'alert_id': alert_id}, {'$set': {'action': 'reconciler_auto_dismissed', 'action_at': datetime.utcnow()}})
                        except Exception:
                            logger.exception('Failed to update reconciler audit')
                    except Exception:
                        logger.exception(f'Failed to auto-dismiss alert {alert_id} by reconciler')

        except Exception:
            logger.exception('Error in alert reconciler loop')

        await asyncio.sleep(interval_seconds)
