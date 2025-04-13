import asyncio
import json
import os
import logging
from dotenv import load_dotenv
from azure.eventhub.aio import EventHubConsumerClient
from flask import Flask, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
# Update CORS to allow ngrok domain
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://7757-103-5-132-9.ngrok-free.app", "http://localhost:3000"],  # Replace with your ngrok URL
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Access-Control-Allow-Origin"],
        "supports_credentials": True
    }
})

# Global variable to store the latest telemetry data
latest_telemetry_data = {
    'voltages': [],
    'currents': [],
    'frequency': [],
    'power': [],  # Added power
    'timestamp': None
}

def validate_connection_string(conn_string: str) -> bool:
    """Validate connection string format"""
    if not conn_string or not isinstance(conn_string, str):
        return False
    
    required_parts = ['Endpoint', 'SharedAccessKeyName', 'SharedAccessKey', 'EntityPath']
    parts = dict(part.split('=', 1) for part in conn_string.split(';') if '=' in part)
    return all(key in parts for key in required_parts)

def load_env_variables():
    load_dotenv()
    required_vars = [
        'EVENTHUB_CONNECTION_STRING',
        'CONSUMER_GROUP',
        'DEVICE_ID'
    ]
    
    env_vars = {var: os.getenv(var) for var in required_vars}
    missing_vars = [var for var in required_vars if not env_vars[var]]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    # Validate connection string
    if not validate_connection_string(env_vars['EVENTHUB_CONNECTION_STRING']):
        raise ValueError("Invalid Event Hub connection string format")
        
    return env_vars

async def process_event(partition_context, event):
    """Handler for IoT Hub events"""
    try:
        device_id = event.system_properties.get(b'iothub-connection-device-id')
        if device_id and device_id.decode() == os.getenv('DEVICE_ID'):
            telemetry_data = json.loads(event.body_as_str())
            logger.info(f"Telemetry from {device_id.decode()}: {telemetry_data}")
            
            # Update global telemetry data
            global latest_telemetry_data
            latest_telemetry_data = telemetry_data
            latest_telemetry_data['timestamp'] = str(datetime.datetime.utcnow())
            
    except Exception as e:
        logger.error(f"Error processing event: {e}")

@app.route('/api/telemetry')
def get_telemetry():
    """REST endpoint to serve the latest telemetry data"""
    telemetry = {
        'voltages': latest_telemetry_data.get('voltages', []),
        'currents': latest_telemetry_data.get('currents', []),
        'frequency': latest_telemetry_data.get('frequency', []),
        'power': latest_telemetry_data.get('power', []),  # Added power
        'timestamp': latest_telemetry_data.get('timestamp'),
        'isConnected': True  # Assume connected if data is being served
    }
    logger.info(f"Sending telemetry data: {telemetry}")
    return jsonify(telemetry)

async def main():
    logger.info("IoT Hub Telemetry Monitor Starting...")
    
    try:
        env_vars = load_env_variables()
        
        # Create EventHub client with custom consumer group
        client = EventHubConsumerClient.from_connection_string(
            env_vars['EVENTHUB_CONNECTION_STRING'],
            consumer_group=env_vars['CONSUMER_GROUP']  # Use custom consumer group
        )
        
        logger.info(f"Starting to monitor telemetry for device: {env_vars['DEVICE_ID']}")
        
        async with client:
            await client.receive(
                on_event=process_event,
                starting_position="-1"  # Start from end of stream
            )
            
    except KeyboardInterrupt:
        logger.info("\nStopping telemetry monitor...")
    except Exception as e:
        logger.error(f"Error in telemetry monitor: {e}")
        raise

if __name__ == "__main__":
    import datetime
    # Run the Flask app in a separate thread
    import threading

    # Install eventlet only when running in production
    if os.environ.get('FLASK_ENV') == 'production':
        import eventlet
        eventlet.monkey_patch()

    def run_app():
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True  # Allow main thread to exit even if app_thread is running
    app_thread.start()

    # Run the main async loop
    asyncio.run(main())


