#!/usr/bin/env python3
"""
Query alerts collection for alerts related to a sensor id using several matching strategies.
Usage:
  python query_alerts_for_sensor.py <SENSOR_ID> [--limit N]

Reads `MONGO_CONNECTION_STRING` and `DATABASE_NAME` from environment.
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

def build_query(sensor_id):
    possible_ids = {sensor_id}
    if "_" in sensor_id:
        possible_ids.add(sensor_id.split("_", 1)[-1])
    if len(sensor_id) >= 12:
        possible_ids.add(sensor_id[-12:])

    or_clauses = []
    for pid in possible_ids:
        or_clauses.append({"sensor_id": pid})
        or_clauses.append({"sensor_id": {"$regex": pid, "$options": "i"}})
        or_clauses.append({"sensor_id": {"$exists": False}, "message": {"$regex": pid, "$options": "i"}})
        or_clauses.append({"location": {"$regex": pid, "$options": "i"}})

    # Also include alerts where type is sensor_disconnection and sensor_id is missing
    or_clauses.append({"type": "sensor_disconnection"})

    return {"$or": or_clauses}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python query_alerts_for_sensor.py <SENSOR_ID> [--limit N]"}))
        sys.exit(1)

    sensor_id = sys.argv[1]
    limit = 50
    if len(sys.argv) >= 3 and sys.argv[2].isdigit():
        limit = int(sys.argv[2])

    MONGO_CONN = os.environ.get('MONGO_CONNECTION_STRING')
    DB_NAME = os.environ.get('DATABASE_NAME') or os.environ.get('MONGO_DB') or 'sampledb'

    if not MONGO_CONN:
        print(json.dumps({"error": "MONGO_CONNECTION_STRING not set in environment"}))
        sys.exit(1)

    client = MongoClient(MONGO_CONN)
    db = client[DB_NAME]
    coll = db.get_collection('alerts')

    query = build_query(sensor_id)

    docs = list(coll.find(query).sort('created_at', -1).limit(limit))

    out = {
        'sensor_id_query': sensor_id,
        'query': query,
        'count_found': len(docs),
        'alerts': []
    }

    for d in docs:
        out['alerts'].append({
            '_id': str(d.get('_id')),
            'type': d.get('type'),
            'level': d.get('level'),
            'sensor_id': d.get('sensor_id'),
            'created_at': iso(d.get('created_at')),
            'resolved_at': iso(d.get('resolved_at')),
            'is_resolved': d.get('is_resolved'),
            'message': d.get('message'),
            'source': d.get('source'),
            'location': d.get('location')
        })

    print(json.dumps(out, indent=2, ensure_ascii=False))
