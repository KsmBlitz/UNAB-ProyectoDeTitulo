"""
Sensors routes
Sensor data and metrics endpoints
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
import logging

from app.config import sensor_collection
from app.utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Datos de Sensores"])


@router.get("/sensors/individual")
async def get_individual_sensors_status(current_user: dict = Depends(get_current_user)):
    """
    Get detailed status of each individual sensor
    
    Returns sensor status based on last reading time:
    - online: < 15 minutes
    - warning: 15-30 minutes
    - offline: > 30 minutes
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        # Find unique sensors and their latest readings
        pipeline = [
            {"$sort": {"ReadTime": -1}},
            {"$group": {
                "_id": "$reservoirId",
                "lastReading": {"$first": "$$ROOT"}
            }},
            {"$limit": 20}
        ]
        
        db_sensors = await sensor_collection.aggregate(pipeline).to_list(length=None)
        sensors = []
        
        for sensor_group in db_sensors:
            reservoir_id = sensor_group["_id"]
            latest_reading = sensor_group["lastReading"]
            
            # Ensure timezone aware datetime
            last_reading_time = latest_reading["ReadTime"]
            if last_reading_time.tzinfo is None:
                last_reading_time = last_reading_time.replace(tzinfo=timezone.utc)
            
            # Calculate time difference
            time_diff = (current_time - last_reading_time).total_seconds()
            minutes_diff = time_diff / 60
            
            # Determine status
            if minutes_diff < 15:
                status = "online"
            elif minutes_diff < 30:
                status = "warning"
            else:
                status = "offline"
            
            sensor_data = {
                "uid": reservoir_id,
                "last_value": {
                    "value": round(latest_reading.get("Temperature", 0), 1),
                    "unit": "°C",
                    "type": "Temperatura"
                },
                "status": status,
                "location": f"Embalse {reservoir_id}",
                "last_reading": last_reading_time.isoformat(),
                "minutes_since_reading": int(minutes_diff)
            }
            
            sensors.append(sensor_data)
        
        return sensors
        
    except Exception as e:
        logger.error(f"Error obteniendo sensores individuales: {e}")
        return []


@router.get("/metrics/latest")
async def get_latest_metrics(
    reservoir_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get latest sensor metrics
    
    Args:
        reservoir_id: Optional filter by reservoir ID
    """
    try:
        query = {}
        if reservoir_id:
            query["reservoirId"] = reservoir_id
        
        # Get latest reading
        latest_reading = await sensor_collection.find_one(
            query,
            sort=[("ReadTime", -1)]
        )
        
        if not latest_reading:
            return {
                "temperature": 0,
                "ph": 0,
                "conductivity": 0,
                "water_level": 0,
                "timestamp": None,
                "reservoir_id": reservoir_id
            }
        
        return {
            "temperature": latest_reading.get("Temperature", 0),
            "ph": latest_reading.get("pH_Value", 0),
            "conductivity": latest_reading.get("EC", 0),
            "water_level": latest_reading.get("Water_Level", 0),
            "timestamp": latest_reading.get("ReadTime"),
            "reservoir_id": latest_reading.get("reservoirId")
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return {
            "temperature": 0,
            "ph": 0,
            "conductivity": 0,
            "water_level": 0,
            "timestamp": None,
            "reservoir_id": reservoir_id
        }


@router.get("/charts/historical-data")
async def get_historical_data(
    reservoir_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=0, le=8760),
    current_user: dict = Depends(get_current_user)
):
    """
    Get historical sensor data for charts
    
    Args:
        reservoir_id: Optional filter by reservoir ID
        hours: Number of hours to retrieve (0 = all data, max 8760 = 1 year)
    """
    try:
        query: Dict[str, Any] = {}
        if reservoir_id:
            query["reservoirId"] = reservoir_id
        
        # Get data from last N hours (0 = all data)
        if hours > 0:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query["ReadTime"] = {"$gte": start_time}
        
        # Fetch data
        cursor = sensor_collection.find(query).sort("ReadTime", 1).limit(1000)
        readings = await cursor.to_list(length=1000)
        
        # Format data for charts - separate arrays for each sensor type
        labels = []
        temperatura_data = []
        ph_data = []
        conductividad_data = []
        nivel_agua_data = []
        
        for reading in readings:
            # Format timestamp
            timestamp = reading.get("ReadTime")
            if timestamp:
                labels.append(timestamp.strftime("%H:%M") if hasattr(timestamp, 'strftime') else str(timestamp))
            else:
                labels.append("")
            
            # Extract values using correct field names
            temperatura_data.append(reading.get("Temperature", 0))
            ph_data.append(reading.get("pH_Value", 0))
            conductividad_data.append(reading.get("EC", 0))
            nivel_agua_data.append(reading.get("Water_Level", 0))
        
        return {
            "labels": labels,
            "temperatura": temperatura_data,
            "ph": ph_data,
            "conductividad": conductividad_data,
            "nivel_agua": nivel_agua_data,
            "count": len(readings),
            "period_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos: {e}")
        return {
            "labels": [],
            "temperatura": [],
            "ph": [],
            "conductividad": [],
            "nivel_agua": [],
            "count": 0,
            "period_hours": hours
        }


@router.get("/sensors/status")
async def get_sensors_status(current_user: dict = Depends(get_current_user)):
    """
    Get current status of all sensors
    
    Returns summary of online/offline sensors
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        # Get unique sensors
        pipeline = [
            {"$sort": {"ReadTime": -1}},
            {"$group": {
                "_id": "$reservoirId",
                "lastReading": {"$first": "$$ROOT"}
            }}
        ]
        
        db_sensors = await sensor_collection.aggregate(pipeline).to_list(length=None)
        
        online_count = 0
        offline_count = 0
        warning_count = 0
        
        for sensor_group in db_sensors:
            latest_reading = sensor_group["lastReading"]
            last_reading_time = latest_reading["ReadTime"]
            
            if last_reading_time.tzinfo is None:
                last_reading_time = last_reading_time.replace(tzinfo=timezone.utc)
            
            minutes_diff = (current_time - last_reading_time).total_seconds() / 60
            
            if minutes_diff < 15:
                online_count += 1
            elif minutes_diff < 30:
                warning_count += 1
            else:
                offline_count += 1
        
        return {
            "online": online_count,
            "warning": warning_count,
            "offline": offline_count,
            "total": online_count + warning_count + offline_count
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de sensores: {e}")
        return {
            "online": 0,
            "warning": 0,
            "offline": 0,
            "total": 0
        }
