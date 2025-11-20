from fastapi import APIRouter, Request, Form, HTTPException
import logging
from datetime import datetime
from typing import Optional

from app.config import notifications_sent_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post('/twilio/status')
async def twilio_status(request: Request):
    """Endpoint for Twilio message status callbacks.
    Twilio posts urlencoded data containing MessageSid, MessageStatus, To, From, ErrorCode, ErrorMessage
    """
    form = await request.form()

    sid = form.get('MessageSid') or form.get('MessageSid')
    status = form.get('MessageStatus') or form.get('MessageStatus')
    to = form.get('To')
    from_ = form.get('From')
    error_code = form.get('ErrorCode')
    error_message = form.get('ErrorMessage')

    if not sid:
        raise HTTPException(status_code=400, detail='Missing MessageSid')

    try:
        # Try to find related notifications_sent record by sid
        existing = await notifications_sent_collection.find_one({'sid': sid})

        update = {
            'status': status,
            'to': to,
            'from': from_,
            'error_code': int(error_code) if error_code and str(error_code).isdigit() else error_code,
            'error_message': error_message,
            'updated_at': datetime.utcnow()
        }

        if existing:
            await notifications_sent_collection.update_one({'_id': existing['_id']}, {'$set': update})
            logger.info(f"Updated Twilio status for sid={sid} status={status} error={error_code}")
        else:
            # Insert a new record if none existed
            doc = {
                'sid': sid,
                'status': status,
                'to': to,
                'from': from_,
                'error_code': int(error_code) if error_code and str(error_code).isdigit() else error_code,
                'error_message': error_message,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'channel': 'whatsapp'
            }
            await notifications_sent_collection.insert_one(doc)
            logger.info(f"Inserted Twilio status record for sid={sid} status={status}")

        return {"success": True}

    except Exception as e:
        logger.exception(f"Error handling Twilio status callback for sid={sid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
