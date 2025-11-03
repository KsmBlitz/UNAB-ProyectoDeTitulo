"""
Prediction service for water quality metrics
Uses simple linear regression to predict pH and EC values for next 5 days
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class WaterQualityPredictor:
    """
    Predictor for water quality metrics using linear regression
    """
    
    def __init__(self):
        self.model = LinearRegression()
        
    def prepare_data(
        self, 
        historical_data: List[Dict]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare historical data for training
        
        Args:
            historical_data: List of sensor readings with ReadTime and value
            
        Returns:
            Tuple of (timestamps as hours from start, values)
        """
        if not historical_data:
            raise ValueError("No historical data provided")
        
        # Sort by time
        sorted_data = sorted(historical_data, key=lambda x: x['ReadTime'])
        
        # Extract timestamps and values
        timestamps = []
        values = []
        
        # Use first reading as reference point (time 0)
        reference_time = sorted_data[0]['ReadTime']
        if isinstance(reference_time, str):
            reference_time = datetime.fromisoformat(reference_time.replace('Z', '+00:00'))
        
        for reading in sorted_data:
            read_time = reading['ReadTime']
            if isinstance(read_time, str):
                read_time = datetime.fromisoformat(read_time.replace('Z', '+00:00'))
            
            # Convert to hours from reference
            hours_from_start = (read_time - reference_time).total_seconds() / 3600
            timestamps.append(hours_from_start)
            values.append(reading['value'])
        
        return np.array(timestamps).reshape(-1, 1), np.array(values)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train the linear regression model
        
        Args:
            X: Input features (timestamps as hours from reference)
            y: Target values
        """
        self.model.fit(X, y)
        # Store the last X value for future predictions
        self.last_X_value = float(X[-1][0])
        
    def predict_next_days(
        self,
        last_timestamp: datetime,
        days: int = 5
    ) -> List[Dict]:
        """
        Predict values for next N days
        
        Args:
            last_timestamp: Last recorded timestamp
            days: Number of days to predict (default: 5)
            
        Returns:
            List of predictions with timestamp and predicted value
        """
        if not hasattr(self, 'last_X_value'):
            raise ValueError("Model must be trained before making predictions")
        
        predictions = []
        
        # Generate future timestamps (one prediction per day)
        for day in range(1, days + 1):
            future_time = last_timestamp + timedelta(days=day)
            
            # Calculate hours from the reference point (used in training)
            # Continue from the last training X value
            hours_from_reference = self.last_X_value + (day * 24)
            
            # Predict
            X_future = np.array([[hours_from_reference]])
            predicted_value = self.model.predict(X_future)[0]
            
            predictions.append({
                'timestamp': future_time,
                'value': round(float(predicted_value), 2)
            })
        
        return predictions


async def predict_sensor_values(
    sensor_collection,
    sensor_type: str,
    days_to_predict: int = 5,
    lookback_days: int = 7
) -> Dict:
    """
    Predict sensor values for next N days
    
    Args:
        sensor_collection: MongoDB collection with sensor data
        sensor_type: Type of sensor ('ph' or 'conductivity')
        days_to_predict: Number of days to predict ahead (default: 5)
        lookback_days: Number of days of historical data to use (default: 7)
        
    Returns:
        Dictionary with predictions and metadata
    """
    try:
        # Map sensor type to field name
        field_mapping = {
            'ph': 'pH',
            'conductivity': 'Conductividad_Electrica'
        }
        
        if sensor_type not in field_mapping:
            raise ValueError(f"Invalid sensor type: {sensor_type}")
        
        field_name = field_mapping[sensor_type]
        
        # Get historical data
        lookback_time = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        cursor = sensor_collection.find({
            "ReadTime": {"$gte": lookback_time},
            field_name: {"$exists": True, "$ne": None}
        }).sort("ReadTime", 1)
        
        historical_readings = await cursor.to_list(length=10000)
        
        if len(historical_readings) < 2:
            logger.warning(f"Insufficient data for {sensor_type} prediction")
            return {
                "success": False,
                "message": "Datos históricos insuficientes para generar predicción",
                "predictions": []
            }
        
        # Prepare data for prediction
        historical_data = [
            {
                'ReadTime': reading['ReadTime'],
                'value': reading[field_name]
            }
            for reading in historical_readings
        ]
        
        # Create and train predictor
        predictor = WaterQualityPredictor()
        X, y = predictor.prepare_data(historical_data)
        
        # Get last reading time
        last_reading_time = historical_data[-1]['ReadTime']
        if isinstance(last_reading_time, str):
            last_reading_time = datetime.fromisoformat(last_reading_time.replace('Z', '+00:00'))
        
        # Train model
        predictor.train(X, y)
        
        # Make predictions using the dedicated method
        predictions = predictor.predict_next_days(
            last_timestamp=last_reading_time,
            days=days_to_predict
        )
        
        # Convert timestamps to ISO format and add day_ahead
        formatted_predictions = []
        for i, pred in enumerate(predictions, 1):
            formatted_predictions.append({
                'timestamp': pred['timestamp'].isoformat() if isinstance(pred['timestamp'], datetime) else pred['timestamp'],
                'value': pred['value'],
                'day_ahead': i
            })
        
        # Get model statistics
        score = predictor.model.score(X, y)
        
        logger.info(f"Generated {len(predictions)} predictions for {sensor_type}")
        
        return {
            "success": True,
            "sensor_type": sensor_type,
            "predictions": formatted_predictions,
            "model_stats": {
                "r2_score": round(float(score), 3),
                "training_samples": len(historical_readings),
                "lookback_days": lookback_days
            },
            "last_reading": {
                "timestamp": last_reading_time.isoformat(),
                "value": round(float(y[-1]), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        return {
            "success": False,
            "message": f"Error generando predicción: {str(e)}",
            "predictions": []
        }
