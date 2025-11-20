#!/usr/bin/env python3
"""
Normalize sensor data timestamps and fill missing sensor_id.

Usage:
  python fix_sensor_data_timestamps.py <RESERVOIR_ID|all>

This script will:
 - For documents in `Sensor_Data` matching the given `reservoirId` (or all),
   set `timestamp` and `created_at` from `ReadTime`/`ProcessedAt` if missing,
   converting naive datetimes (assumed America/Santiago) to UTC-aware datetimes.
 - If `sensor_id` is null and `raw.SensorID` exists, set `sensor_id` accordingly.

Run inside the backend container so environment vars are available (MONGO_CONNECTION_STRING, DATABASE_NAME).
"""
import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from pymongo import MongoClient
except Exception as e:
    print(json.dumps({"error": f"pymongo not available: {e}"}))
    sys.exit(1)


def parse_iso(s: str):
    if not s:
        return None
    try:
        # datetime.fromisoformat handles microseconds when present
        return datetime.fromisoformat(s)
    except Exception:
        return None


def to_utc_aware(dt: datetime):
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume Chile local time for legacy naive timestamps
        local = ZoneInfo("America/Santiago")
        dt = dt.replace(tzinfo=local)
    return dt.astimezone(ZoneInfo("UTC"))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python fix_sensor_data_timestamps.py <RESERVOIR_ID|all>"}))
        sys.exit(1)

    target = sys.argv[1]

    MONGO_CONN = os.environ.get('MONGO_CONNECTION_STRING')
    DB_NAME = os.environ.get('DATABASE_NAME') or os.environ.get('MONGO_DB') or 'sampledb'

    if not MONGO_CONN:
        print(json.dumps({"error": "MONGO_CONNECTION_STRING not set in environment"}))
        sys.exit(1)

    client = MongoClient(MONGO_CONN)
    db = client[DB_NAME]
    coll = db.get_collection('Sensor_Data')

    if target.lower() == 'all':
        query = {}
    else:
        query = {"$or": [{"reservoirId": target}, {"sensor_id": target}, {"reservoir_id": target}]}

    cursor = coll.find(query)
    processed = 0
    updated = 0

    for doc in cursor:
        processed += 1
        updates = {}

        # Fill sensor_id from raw.SensorID if missing
        if not doc.get('sensor_id'):
            raw = doc.get('raw') or {}
            raw_sensor = raw.get('SensorID') or (raw.get('SensorID') if isinstance(raw, dict) else None)
            if raw_sensor:
                updates['sensor_id'] = raw_sensor

        # Determine a reliable timestamp source: ReadTime -> ProcessedAt -> RawMessage.timestamp -> raw.Timestamp
        ts = doc.get('timestamp')
        if not ts:
            candidate = None
            for key in ('ReadTime', 'ProcessedAt'):
                val = doc.get(key) or (doc.get('raw') or {}).get(key)
                if val:
                    candidate = val
                    break

            if not candidate:
                # Try nested raw.RawMessage.timestamp or raw.Timestamp
                raw = doc.get('raw') or {}
                candidate = (raw.get('RawMessage') or {}).get('timestamp') or raw.get('Timestamp')

            parsed = None
            if isinstance(candidate, datetime):
                parsed = candidate
            else:
                parsed = parse_iso(candidate) if candidate else None

            if parsed:
                ts_utc = to_utc_aware(parsed)
                if ts_utc:
                    updates['timestamp'] = ts_utc

        # created_at fallback
        if not doc.get('created_at'):
            if updates.get('timestamp'):
                updates['created_at'] = updates['timestamp']
            else:
                # fallback to ReadTime if present
                rt = doc.get('ReadTime')
                if isinstance(rt, datetime):
                    updates['created_at'] = to_utc_aware(rt)
                else:
                    parsed_rt = parse_iso(rt) if rt else None
                    if parsed_rt:
                        updates['created_at'] = to_utc_aware(parsed_rt)

        if updates:
            res = coll.update_one({'_id': doc['_id']}, {'$set': updates})
            updated += 1 if (res.modified_count and res.modified_count > 0) else 0

    out = {
        'processed': processed,
        'updated': updated,
        'note': 'Timestamps set to UTC-aware datetimes (assumed America/Santiago for naive values).'
    }
    print(json.dumps(out, default=str, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
