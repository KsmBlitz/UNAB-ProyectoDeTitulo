#!/usr/bin/env python3
"""
Collect alerts and notification summaries from MongoDB and print as JSON.
This script expects environment variables `MONGO_CONNECTION_STRING` and `DATABASE_NAME` to be available
inside the container (the same environment used by the backend). It prints a JSON document to stdout.
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

MONGO_CONN = os.environ.get("MONGO_CONNECTION_STRING")
DB_NAME = os.environ.get("DATABASE_NAME") or os.environ.get("MONGO_DB") or "sampledb"

if not MONGO_CONN:
    print(json.dumps({"error": "MONGO_CONNECTION_STRING not set in environment"}))
    sys.exit(1)

client = MongoClient(MONGO_CONN)
db = client[DB_NAME]

def iso(dt):
    if dt is None:
        return None
    if hasattr(dt, 'isoformat'):
        return dt.isoformat()
    return str(dt)

report = {}

# Active alerts (sample)
alerts_coll = db.get_collection('alerts')
notifications_coll = db.get_collection('notifications_sent')

active_cursor = alerts_coll.find({'is_resolved': False}, {'type':1,'level':1,'created_at':1,'sensor_id':1,'source':1}).sort('created_at', -1).limit(50)
report['active_alerts_sample'] = []
for d in active_cursor:
    report['active_alerts_sample'].append({
        'id': str(d.get('_id')),
        'type': d.get('type'),
        'level': d.get('level'),
        'created_at': iso(d.get('created_at')),
        'sensor_id': d.get('sensor_id'),
        'source': d.get('source')
    })

# Counts by level and type for unresolved
pipeline = [
    {'$match': {'is_resolved': False}},
    {'$group': {'_id': {'level': '$level', 'type': '$type'}, 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
grouped = list(alerts_coll.aggregate(pipeline))
report['active_counts'] = grouped

# Notifications recent
notif_cursor = notifications_coll.find({}).sort('sent_at', -1).limit(50)
report['notifications_recent'] = []
for n in notif_cursor:
    report['notifications_recent'].append({
        'id': str(n.get('_id')),
        'alert_id': str(n.get('alert_id')) if n.get('alert_id') else None,
        'channel': n.get('channel'),
        'sent_at': iso(n.get('sent_at')),
        'status': n.get('status') if 'status' in n else None,
        'to': n.get('to')
    })

# Quick sanity check timestamps: last notification time vs last alert created
last_alert = alerts_coll.find_one(sort=[('created_at', -1)])
last_notif = notifications_coll.find_one(sort=[('sent_at', -1)])
report['last_alert_created_at'] = iso(last_alert.get('created_at')) if last_alert else None
report['last_notification_sent_at'] = iso(last_notif.get('sent_at')) if last_notif else None

print(json.dumps(report, indent=2, ensure_ascii=False))
