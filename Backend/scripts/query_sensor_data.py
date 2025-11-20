#!/usr/bin/env python3
"""
Query latest sensor readings for a given sensor id and print JSON.
Usage:
  python query_sensor_data.py <SENSOR_ID> [--limit N]

The script reads `MONGO_CONNECTION_STRING` and `DATABASE_NAME` from environment.
"""
import os
import sys
import json
from datetime import datetime

try:
    from pymongo import MongoClient
except Exception as e:
    print(json.dumps({"error": "pymongo not available: %s" % str(e)}))
    sys.exit(1)

def iso(dt):
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


def sanitize(obj):
    """Recursively convert datetimes in obj to ISO strings so JSON can serialize it."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python query_sensor_data.py <SENSOR_ID> [--limit N]"}))
        sys.exit(1)

    sensor_id = sys.argv[1]
    limit = 20
    if len(sys.argv) >= 3 and sys.argv[2].isdigit():
        limit = int(sys.argv[2])

    MONGO_CONN = os.environ.get('MONGO_CONNECTION_STRING')
    DB_NAME = os.environ.get('DATABASE_NAME') or os.environ.get('MONGO_DB') or 'sampledb'

    if not MONGO_CONN:
        print(json.dumps({"error": "MONGO_CONNECTION_STRING not set in environment"}))
        sys.exit(1)

    client = MongoClient(MONGO_CONN)
    db = client[DB_NAME]
    coll = db.get_collection('Sensor_Data')

    query = {
        "$or": [
            {"reservoirId": sensor_id},
            {"sensor_id": sensor_id},
            {"reservoir_id": sensor_id}
        ]
    }

    docs = list(coll.find(query).sort('ReadTime', -1).limit(limit))

    out = {
        "sensor_id": sensor_id,
        "count_found": len(docs),
        "samples": []
    }

    for d in docs:
        sample = {
            "_id": str(d.get('_id')),
            "reservoirId": d.get('reservoirId'),
            "sensor_id": d.get('sensor_id'),
            "ReadTime": iso(d.get('ReadTime')),
            "created_at": iso(d.get('created_at')),
            "timestamp": iso(d.get('timestamp')),
            "ph": d.get('ph') or d.get('pH') or d.get('PH') or d.get('pH_Value'),
            "ec": d.get('ec') or d.get('EC') or d.get('conductivity'),
            "temperature": d.get('temperature') or d.get('temp') or d.get('TEMP'),
            "raw": {k: v for k, v in d.items() if k not in ['_id']}
        }
        out['samples'].append(sample)

    print(json.dumps(sanitize(out), indent=2, ensure_ascii=False))
