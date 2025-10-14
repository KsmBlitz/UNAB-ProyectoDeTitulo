# Backend/aws_iot_client.py

import json
import asyncio
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone
from awsiot import mqtt_connection_builder
from awscrt import io, mqtt
import threading

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSIoTClient:
    def __init__(self, 
                 endpoint: str,
                 root_ca_path: str,
                 certificate_path: str,
                 private_key_path: str,
                 client_id: str = "FastAPI_Consumer"):
        
        self.endpoint = endpoint
        self.root_ca_path = root_ca_path
        self.certificate_path = certificate_path
        self.private_key_path = private_key_path
        self.client_id = client_id
        
        self.mqtt_connection = None
        self.event_loop_group = None
        self.host_resolver = None
        self.client_bootstrap = None
        self.is_connected = False
        
        # Callback para procesar mensajes recibidos
        self.message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Establece la función callback para procesar mensajes"""
        self.message_callback = callback
        
    def connect(self) -> bool:
        """Conecta al broker AWS IoT Core"""
        try:
            logger.info(f"Conectando a AWS IoT Core: {self.endpoint}")
            
            # Configurar el event loop y bootstrap
            self.event_loop_group = io.EventLoopGroup(1)
            self.host_resolver = io.DefaultHostResolver(self.event_loop_group)
            self.client_bootstrap = io.ClientBootstrap(self.event_loop_group, self.host_resolver)
            
            # Crear la conexión MQTT
            self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self.endpoint,
                cert_filepath=self.certificate_path,
                pri_key_filepath=self.private_key_path,
                client_bootstrap=self.client_bootstrap,
                ca_filepath=self.root_ca_path,
                client_id=self.client_id,
                clean_session=False,
                keep_alive_secs=30,
                on_connection_interrupted=self._on_connection_interrupted,
                on_connection_resumed=self._on_connection_resumed
            )
            
            # Conectar
            connect_future = self.mqtt_connection.connect()
            connect_future.result()
            
            self.is_connected = True
            logger.info("✅ Conectado exitosamente a AWS IoT Core")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a AWS IoT Core: {e}")
            return False
    
    def subscribe_to_topic(self, topic: str) -> bool:
        """Suscribirse a un tópico MQTT"""
        if not self.is_connected or self.mqtt_connection is None:
            logger.error("No hay conexión activa con AWS IoT Core")
            return False
            
        try:
            logger.info(f"Suscribiéndose al tópico: {topic}")
            
            subscribe_future, _ = self.mqtt_connection.subscribe(
                topic=topic,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self._on_message_received
            )
            
            subscribe_result = subscribe_future.result()
            logger.info(f"✅ Suscrito exitosamente al tópico: {topic}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error suscribiéndose al tópico {topic}: {e}")
            return False
    
    def _on_message_received(self, topic: str, payload: bytes, dup: bool, qos: mqtt.QoS, retain: bool):
        """Callback interno para procesar mensajes recibidos"""
        try:
            # Decodificar el payload JSON
            message_data = json.loads(payload.decode('utf-8'))
            
            logger.info(f"📡 Mensaje recibido en {topic}: {message_data}")
            
            # Extraer reservoirId del tópico (formato: sensor/reservoirId/data)
            topic_parts = topic.split('/')
            reservoir_id = topic_parts[1] if len(topic_parts) >= 3 else "unknown"
            
            # Preparar los datos para el callback
            sensor_data = {
                'reservoirId': reservoir_id,
                'topic': topic,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'raw_data': message_data,
                **message_data  # Incluir todos los campos del mensaje
            }
            
            # Llamar al callback si está configurado
            if self.message_callback:
                # Ejecutar el callback en un hilo separado para no bloquear MQTT
                threading.Thread(
                    target=self._execute_callback_safely,
                    args=(sensor_data,),
                    daemon=True
                ).start()
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando JSON del tópico {topic}: {e}")
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje del tópico {topic}: {e}")
    
    def _execute_callback_safely(self, sensor_data: Dict[str, Any]):
        """Ejecuta el callback de forma segura"""
        try:
            if self.message_callback is not None:
                self.message_callback(sensor_data)
        except Exception as e:
            logger.error(f"❌ Error en callback de mensaje: {e}")
    
    def _on_connection_interrupted(self, connection, error, **kwargs):
        """Callback para conexión interrumpida"""
        logger.warning(f"⚠️ Conexión AWS IoT interrumpida: {error}")
        self.is_connected = False
    
    def _on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        """Callback para conexión restablecida"""
        logger.info(f"🔄 Conexión AWS IoT restablecida: {return_code}")
        self.is_connected = True
    
    def disconnect(self):
        """Desconectar del broker AWS IoT Core"""
        if self.mqtt_connection and self.is_connected:
            try:
                logger.info("Desconectando de AWS IoT Core...")
                disconnect_future = self.mqtt_connection.disconnect()
                disconnect_future.result()
                self.is_connected = False
                logger.info("✅ Desconectado exitosamente de AWS IoT Core")
            except Exception as e:
                logger.error(f"❌ Error desconectando: {e}")
    
    def __del__(self):
        """Cleanup al destruir el objeto"""
        self.disconnect()


class IoTDataProcessor:
    """Clase para procesar y validar datos de sensores IoT"""
    
    @staticmethod
    def process_sensor_message(sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa y normaliza un mensaje de sensor IoT
        
        Args:
            sensor_data: Datos del sensor desde AWS IoT Core
            
        Returns:
            Datos procesados listos para MongoDB
        """
        try:
            # Extraer datos del mensaje
            raw_data = sensor_data.get('raw_data', {})
            reservoir_id = sensor_data.get('reservoirId', 'unknown')
            
            # Mapear campos del sensor (ajusta según tu formato de datos)
            processed_data = {
                'reservoirId': reservoir_id,
                'SensorID': f"AWS_IoT_{reservoir_id}",
                'ReadTime': datetime.now(timezone.utc),
                'Timestamp': sensor_data.get('timestamp'),
                'Topic': sensor_data.get('topic', ''),
                
                # Campos de sensores - ajusta según tus nombres de campos
                'Temperature': raw_data.get('temperature', raw_data.get('temp', 0.0)),
                'EC': raw_data.get('ec', raw_data.get('conductivity', 0.0)),
                'pH_Value': raw_data.get('ph', raw_data.get('pH', raw_data.get('ph_value', 7.0))),
                'Water_Level': raw_data.get('water_level', raw_data.get('level', 0.0)),
                
                # Metadatos adicionales
                'Source': 'AWS_IoT_Core',
                'ProcessedAt': datetime.now(timezone.utc).isoformat(),
                'RawMessage': raw_data
            }
            
            logger.info(f"✅ Datos procesados para {reservoir_id}: T={processed_data['Temperature']}°C, pH={processed_data['pH_Value']}, EC={processed_data['EC']}")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos del sensor: {e}")
            raise


# Función de utilidad para crear y configurar el cliente
def create_iot_client(settings) -> AWSIoTClient:
    """Crea y configura un cliente AWS IoT Core"""
    return AWSIoTClient(
        endpoint=settings.AWS_IOT_ENDPOINT,
        root_ca_path=settings.AWS_IOT_ROOT_CA_PATH,
        certificate_path=settings.AWS_IOT_CERTIFICATE_PATH,
        private_key_path=settings.AWS_IOT_PRIVATE_KEY_PATH,
        client_id=settings.AWS_IOT_CLIENT_ID
    )