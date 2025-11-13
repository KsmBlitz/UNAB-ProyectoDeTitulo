"""
Migration script: normalize alert documents in `alerts` and `alert_history` collections.
- Ensure `created_at`, `resolved_at`, `dismissed_at` are timezone-aware (UTC) when storing or reading.
- Ensure `alert_history` documents have `alert_id` (string) and `resolution_type` (non-null string).
- For `alerts`, ensure `created_at` is timezone-aware and `id` field exists (string of _id).

Run inside backend container: `python3 /app/scripts/migrate_alert_history.py`
"""

from datetime import datetime, timezone
from pymongo import MongoClient
import os

MONGO_URI = os.environ.get('MONGO_URI') or os.environ.get('MONGO_CONNECTION_STRING') or 'mongodb://mongo:27017'
DB_NAME = os.environ.get('MONGO_DB') or os.environ.get('DATABASE_NAME') or 'SampleDatabase'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

alerts = db['alerts']
history = db['alert_history']

def make_dt_aware(dt):
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt
    try:
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return dt


def migrate_alerts(limit=1000):
    count = 0
    for doc in alerts.find().limit(limit):
        updates = {}
        _id = doc.get('_id')
        # Ensure created_at is tz-aware
        ca = doc.get('created_at')
        new_ca = make_dt_aware(ca)
        if new_ca is not None and new_ca != ca:
            updates['created_at'] = new_ca
        # Ensure string id exists
        if not doc.get('id'):
            updates['id'] = str(_id)
        if updates:
            alerts.update_one({'_id': _id}, {'$set': updates})
            count += 1
    print(f"Alerts migrated: {count}")


def migrate_history(limit=1000):
    count = 0
    for doc in history.find().limit(limit):
        updates = {}
        _id = doc.get('_id')
        # Ensure alert_id exists
        if not doc.get('alert_id'):
            # If original stored the full alert doc in 'alert' field with _id
            if doc.get('alert') and isinstance(doc.get('alert'), dict) and doc['alert'].get('_id'):
                updates['alert_id'] = str(doc['alert']['_id'])
            else:
                updates['alert_id'] = str(_id)
        # resolution_type fallback
        if not doc.get('resolution_type'):
            if doc.get('resolution'):
                updates['resolution_type'] = doc.get('resolution')
            else:
                updates['resolution_type'] = 'manual_dismiss'
        # Timezone-aware datetimes
        for field in ('created_at', 'dismissed_at', 'resolved_at', 'archived_at'):
            val = doc.get(field)
            new_val = make_dt_aware(val)
            if new_val is not None and new_val != val:
                updates[field] = new_val
        if updates:
            history.update_one({'_id': _id}, {'$set': updates})
            count += 1
    print(f"History migrated: {count}")


if __name__ == '__main__':
    print('Starting migration...')
    migrate_alerts()
    migrate_history()
    print('Migration finished.')
