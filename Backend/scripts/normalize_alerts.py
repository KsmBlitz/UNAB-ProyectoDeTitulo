#!/usr/bin/env python3
"""
Normalize alert documents in MongoDB:
- Standardize `type` and `level` fields to canonical values
- Convert naive datetimes (assumed Chile time UTC-3) to UTC-aware timestamps

Usage:
  # Dry run (no writes)
  python Backend/scripts/normalize_alerts.py

  # Apply changes
  python Backend/scripts/normalize_alerts.py --apply

Run inside the backend container (recommended) where env vars are available:
  docker-compose exec backend python /app/Backend/scripts/normalize_alerts.py --apply

The script is conservative and logs each planned update. Default is dry-run.
"""
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
try:
    from pymongo import MongoClient
except Exception as e:
    print("pymongo is required. Run this inside the backend container or install pymongo.")
    raise


CHILE_OFFSET = timedelta(hours=-3)

# Mappings to canonical values
TYPE_MAP = {
    'sensor_disconnected': 'sensor_disconnection',
    'disconnected': 'sensor_disconnection',
    'offline': 'sensor_disconnection',
    'ph_value': 'ph', 'pH_Value': 'ph', 'PH': 'ph', 'pH': 'ph',
    'EC': 'ec', 'ec': 'ec', 'conductivity': 'ec', 'Conductivity': 'ec',
    'temp': 'temperature', 'TEMP': 'temperature', 'Temperature': 'temperature',
    'waterLevel': 'water_level', 'water_level': 'water_level', 'nivel_agua': 'water_level',
}

LEVEL_MAP = {
    'crítico': 'critical', 'critico': 'critical', 'crítica': 'critical', 'critical': 'critical',
    'advertencia': 'warning', 'warning': 'warning',
    'info': 'info', 'información': 'info', 'informacion': 'info'
}


def load_env_path(repo_root: Path) -> None:
    # Try to load Backend/.env and export MONGO_CONNECTION_STRING if not set
    env_path = repo_root / 'Backend' / '.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip().startswith('MONGO_CONNECTION_STRING'):
                val = line.split('=', 1)[1].strip().strip('"')
                os.environ.setdefault('MONGO_CONNECTION_STRING', val)
            if line.strip().startswith('DATABASE_NAME'):
                val = line.split('=', 1)[1].strip().strip('"')
                os.environ.setdefault('DATABASE_NAME', val)


def make_aware(dt):
    """If dt is naive, assume Chile time (UTC-3) and convert to UTC-aware datetime."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            # Try ISO parse
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except Exception:
            return None
    if getattr(dt, 'tzinfo', None) is None:
        try:
            local = dt.replace(tzinfo=timezone(CHILE_OFFSET))
            return local.astimezone(timezone.utc)
        except Exception:
            return dt.replace(tzinfo=timezone.utc)
    else:
        return dt.astimezone(timezone.utc)


def canonical_type(t):
    if not t:
        return t
    return TYPE_MAP.get(t, t)


def canonical_level(l):
    if not l:
        return l
    return LEVEL_MAP.get(l, l)


def process_collection(coll, apply=False):
    total = 0
    updated = 0
    for doc in coll.find({}):
        total += 1
        _id = doc.get('_id')
        updates = {}

        # Normalize type
        t = doc.get('type')
        can_t = canonical_type(t)
        if can_t != t:
            updates['type'] = can_t

        # Normalize level
        l = doc.get('level')
        can_l = canonical_level(l)
        if can_l != l:
            updates['level'] = can_l

        # Normalize created_at/resolved_at/dismissed_at
        for field in ('created_at', 'resolved_at', 'dismissed_at', 'ReadTime'):
            if field in doc and doc.get(field) is not None:
                aware = make_aware(doc.get(field))
                if aware is not None:
                    # Store normalized field as UTC datetime
                    if field == 'ReadTime':
                        # keep original field name
                        if aware != doc.get(field):
                            updates[field] = aware
                    else:
                        if aware != doc.get(field):
                            updates[field] = aware

        if updates:
            print(f"Doc {_id} updates: {updates}")
            if apply:
                coll.update_one({'_id': _id}, {'$set': updates})
                updated += 1

    print(f"Processed {total} documents in {coll.name}. Applied updates: {updated}")
    return total, updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply changes to DB')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    load_env_path(repo_root)

    MONGO = os.getenv('MONGO_CONNECTION_STRING')
    DBNAME = os.getenv('DATABASE_NAME', 'SampleDatabase')

    if not MONGO:
        print('MONGO_CONNECTION_STRING not found in environment or Backend/.env')
        sys.exit(1)

    client = MongoClient(MONGO)
    db = client.get_database(DBNAME)

    alerts = db.get_collection('alerts')
    history = db.get_collection('alert_history')

    print('Connected to', DBNAME)

    print('\nInspecting `alerts` collection (dry-run=%s)' % (not args.apply))
    process_collection(alerts, apply=args.apply)

    print('\nInspecting `alert_history` collection (dry-run=%s)' % (not args.apply))
    process_collection(history, apply=args.apply)

    print('\nDone.')


if __name__ == '__main__':
    main()
