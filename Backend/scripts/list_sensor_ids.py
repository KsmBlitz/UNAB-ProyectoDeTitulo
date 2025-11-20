#!/usr/bin/env python3
"""
List distinct sensor identifiers in the `Sensor_Data` collection with counts and last ReadTime.
Prints JSON with the top N sensors by count.

Usage:
  python list_sensor_ids.py [--limit N]

Requires `MONGO_CONNECTION_STRING` and `DATABASE_NAME` in environment.
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

def main():
    limit = 50
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit = int(sys.argv[1])

    MONGO_CONN = os.environ.get('MONGO_CONNECTION_STRING')
    DB_NAME = os.environ.get('DATABASE_NAME') or os.environ.get('MONGO_DB') or 'sampledb'

    if not MONGO_CONN:
        print(json.dumps({"error": "MONGO_CONNECTION_STRING not set in environment"}))
        sys.exit(1)

    client = MongoClient(MONGO_CONN)
    db = client[DB_NAME]
    coll = db.get_collection('Sensor_Data')

    pipeline = [
        {"$project": {"reservoirId": 1, "sensor_id": 1, "ReadTime": 1, "created_at": 1}},
        {"$group": {"_id": {"reservoirId": "$reservoirId", "sensor_id": "$sensor_id"}, "count": {"$sum": 1}, "lastRead": {"$max": "$ReadTime"}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]

    try:
        results = list(coll.aggregate(pipeline))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    out = []
    for r in results:
        key = r.get('_id') or {}
        out.append({
            'reservoirId': key.get('reservoirId'),
            'sensor_id': key.get('sensor_id'),
            'count': r.get('count'),
            'lastRead': iso(r.get('lastRead'))
        })

    print(json.dumps({'top_sensors': out}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
