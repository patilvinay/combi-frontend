import asyncio
import json
import os
import logging
import datetime
from datetime import timedelta
import signal
import sys
import threading
from collections import defaultdict
from dotenv import load_dotenv
from azure.eventhub.aio import EventHubConsumerClient
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ARRAY, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Configuration
load_dotenv()  # Make sure this is called before accessing env variables

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

# For your current hardcoded values in the code, it should be:
DATABASE_URL = "postgresql://postgres:12345@localhost:5432/day_number"  # Your current configuration

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Database Model
class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    voltages = Column(ARRAY(Float))
    currents = Column(ARRAY(Float))
    frequency = Column(ARRAY(Float))
    power = Column(ARRAY(Float))
    power_factor = Column(ARRAY(Float))  # Moved power_factor immediately after power
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_connected = Column(Boolean, default=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Flask app setup
app = Flask(__name__, static_folder='static')
# Update CORS to allow ngrok domain
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],  # Allow all origins for testing
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Access-Control-Allow-Origin"],
        "supports_credentials": True
    }
})

# Create static folder if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)

# Global dictionary to store telemetry data for multiple devices
device_telemetry_data = defaultdict(lambda: {
    'voltages': [],
    'currents': [],
    'frequency': [],
    'power': [],
    'power_factor': [],
    'timestamp': None,
    'device_id': None
})

# Dictionary to track the last time data was stored for each device
last_storage_time = {}

# Dictionary to buffer telemetry data between storage intervals
telemetry_buffer = {}

# Create a background task to handle periodic storage
async def periodic_storage_task():
    """Background task to ensure data is stored every 20 seconds"""
    while True:
        try:
            current_time = datetime.datetime.now().timestamp()

            # Check each device's buffer
            for device_id, buffer in list(telemetry_buffer.items()):
                if not buffer:  # Skip empty buffers
                    continue

                last_time = last_storage_time.get(device_id, 0)

                # If 20 seconds have passed since last storage, store the data
                if current_time - last_time >= 20:  # Changed from 5 to 20 seconds
                    logger.info(f"Periodic task: Storing buffered data for device {device_id}")

                    # Get the latest data from the buffer
                    latest_data = buffer[-1]

                    # Store in database
                    await manage_rolling_data(device_id, latest_data)

                    # Update the last storage time
                    last_storage_time[device_id] = current_time

                    # Clear the buffer
                    telemetry_buffer[device_id] = []

            # Sleep for a short time to avoid high CPU usage
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in periodic storage task: {e}", exc_info=True)
            await asyncio.sleep(5)  # Sleep longer on error

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
        'DEVICE_ID'  # Add DEVICE_ID to the required variables
    ]

    env_vars = {var: os.getenv(var) for var in required_vars}
    missing_vars = [var for var in required_vars if not env_vars[var]]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    if not validate_connection_string(env_vars['EVENTHUB_CONNECTION_STRING']):
        raise ValueError("Invalid Event Hub connection string format")

    return env_vars

async def manage_rolling_data(device_id: str, telemetry_data: dict):
    """Manage continuous data storage with rolling deletion of older data"""
    try:
        db = SessionLocal()
        current_time = datetime.datetime.now(datetime.timezone.utc)

        # Insert new data
        new_telemetry = TelemetryData(
            device_id=device_id,
            voltages=telemetry_data.get('voltages', []),
            currents=telemetry_data.get('currents', []),
            frequency=telemetry_data.get('frequency', []),
            power=telemetry_data.get('power', []),
            power_factor=telemetry_data.get('power_factor', []),
            timestamp=current_time,
            is_connected=True
        )
        db.add(new_telemetry)
        logger.info(f"Added new telemetry data for device {device_id}")

        # Commit the new data
        db.commit()

        # Calculate the cutoff timestamps for the last two days
        # two_days_ago = current_time - timedelta(days=2)
        two_days_ago = current_time - timedelta(days=2)
        

        # Delete data older than two days for this device
        deleted_count = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id,
            TelemetryData.timestamp < two_days_ago
        ).delete()
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old records for device {device_id} (older than {two_days_ago})")

        # Commit the deletion
        db.commit()

    except Exception as e:
        logger.error(f"Error managing data storage: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

async def process_event(partition_context, event):
    """Handler for IoT Hub events"""
    try:
        # Log the raw event for debugging
        logger.debug(f"Received event: {event.body_as_str()}")
        logger.debug(f"Event system properties: {event.system_properties}")

        device_id = event.system_properties.get(b'iothub-connection-device-id')
        if device_id:
            decoded_device_id = device_id.decode()
            logger.info(f"Processing event from device: {decoded_device_id}")

            # Parse the event body
            telemetry_data = json.loads(event.body_as_str())
            logger.debug(f"Parsed telemetry data: {telemetry_data}")

            # Check if the expected fields are present
            if not any(key in telemetry_data for key in ['voltages', 'currents', 'frequency', 'power', 'power_factor']):
                logger.warning(f"Event does not contain expected telemetry fields. Event data: {telemetry_data}")

                # Try to extract data from different formats
                # Format 1: Single values instead of arrays
                voltages = []
                currents = []
                frequency = []
                power = []
                power_factor = []

                if 'voltage' in telemetry_data:
                    voltages = [float(telemetry_data['voltage'])]
                    logger.info(f"Found single voltage value: {voltages}")

                if 'current' in telemetry_data:
                    currents = [float(telemetry_data['current'])]
                    logger.info(f"Found single current value: {currents}")

                if 'freq' in telemetry_data:
                    frequency = [float(telemetry_data['freq'])]
                    logger.info(f"Found single frequency value: {frequency}")

                if 'pwr' in telemetry_data:
                    power = [float(telemetry_data['pwr'])]
                    logger.info(f"Found single power value: {power}")

                if 'power_factor' in telemetry_data:
                    power_factor = [float(telemetry_data['power_factor'])]
                    logger.info(f"Found single power factor value: {power_factor}")

                # Update with the extracted values
                device_telemetry_data[decoded_device_id].update({
                    'voltages': voltages,
                    'currents': currents,
                    'frequency': frequency,
                    'power': power,
                    'power_factor': power_factor,
                    'timestamp': str(datetime.datetime.now(datetime.timezone.utc)),
                    'device_id': decoded_device_id,
                    'isConnected': True
                })

                # Create a compatible format for database storage
                compatible_telemetry = {
                    'voltages': voltages,
                    'currents': currents,
                    'frequency': frequency,
                    'power': power,
                    'power_factor': power_factor
                }

                # Add to buffer for periodic storage
                if decoded_device_id not in telemetry_buffer:
                    telemetry_buffer[decoded_device_id] = []

                telemetry_buffer[decoded_device_id].append(compatible_telemetry)
                logger.debug(f"Added data to buffer for device {decoded_device_id} (will be stored on next 20-second interval)")

            else:
                # Original format with arrays
                logger.info(f"Processing standard format telemetry data")

                # Store in memory (for immediate access)
                device_telemetry_data[decoded_device_id].update({
                    'voltages': telemetry_data.get('voltages', []),
                    'currents': telemetry_data.get('currents', []),
                    'frequency': telemetry_data.get('frequency', []),
                    'power': telemetry_data.get('power', []),
                    'power_factor': telemetry_data.get('power_factor', []),
                    'timestamp': str(datetime.datetime.now(datetime.timezone.utc)),
                    'device_id': decoded_device_id,
                    'isConnected': True
                })

                # Add to buffer for periodic storage
                if decoded_device_id not in telemetry_buffer:
                    telemetry_buffer[decoded_device_id] = []

                telemetry_buffer[decoded_device_id].append(telemetry_data)
                logger.debug(f"Added data to buffer for device {decoded_device_id} (will be stored on next 20-second interval)")

            await partition_context.update_checkpoint(event)
        else:
            logger.warning("Received event without device ID")

    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/telemetry')
def get_telemetry():
    """REST endpoint to serve telemetry data for all devices"""
    devices_data = {
        device_id: {
            'voltages': data.get('voltages', []),
            'currents': data.get('currents', []),
            'frequency': data.get('frequency', []),
            'power': data.get('power', []),
            'power_factor': data.get('power_factor', []),
            'timestamp': data.get('timestamp'),
            'isConnected': True,
            'device_id': device_id
        }
        for device_id, data in device_telemetry_data.items()
    }
    return jsonify(devices_data)

@app.route('/api/telemetry/<device_id>')
def get_device_telemetry(device_id):
    """REST endpoint to serve telemetry data for a specific device"""
    try:
        db = SessionLocal()

        # Get the latest record for this device
        latest_record = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id
        ).order_by(TelemetryData.timestamp.desc()).first()

        if not latest_record:
            return jsonify({
                'error': f"No data found for device {device_id}",
                'available_devices': []
            }), 404

        # Prepare the response with the latest data
        response_data = {
            'voltages': latest_record.voltages or [],
            'currents': latest_record.currents or [],
            'frequency': latest_record.frequency or [],
            'power': latest_record.power or [],
            'power_factor': latest_record.power_factor or [],
            'timestamp': str(latest_record.timestamp),
            'isConnected': latest_record.is_connected,
            'device_id': device_id
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error retrieving telemetry: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()

@app.route('/api/telemetry/<device_id>/all')
def get_all_device_telemetry(device_id):
    """REST endpoint to serve all telemetry data for a specific device"""
    try:
        db = SessionLocal()

        # Get all records for this device, ordered by timestamp
        all_records = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id
        ).order_by(TelemetryData.timestamp).all()

        if not all_records:
            return jsonify({
                'error': f"No data found for device {device_id}",
                'available_devices': []
            }), 404

        # Format all records' data
        records_data = []
        for record in all_records:
            records_data.append({
                'voltages': record.voltages or [],
                'currents': record.currents or [],
                'frequency': record.frequency or [],
                'power': record.power or [],
                'power_factor': record.power_factor or [],
                'timestamp': str(record.timestamp),
                'isConnected': record.is_connected,
                'device_id': device_id
            })

        return jsonify({
            'device_id': device_id,
            'records': records_data,
            'total_records': len(records_data)
        })

    except Exception as e:
        logger.error(f"Error retrieving telemetry: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()

@app.route('/api/test-telemetry', methods=['POST'])
def test_telemetry():
    """Test endpoint to manually inject telemetry data"""
    try:
        data = request.json
        if not data or not data.get('device_id'):
            return jsonify({'error': 'Missing device_id in request'}), 400

        device_id = data.get('device_id')
        logger.info(f"Received test telemetry for device {device_id}")

        # Extract telemetry values with defaults
        voltages = data.get('voltages', []) or data.get('voltage', [])
        if isinstance(voltages, (int, float)):
            voltages = [float(voltages)]

        currents = data.get('currents', []) or data.get('current', [])
        if isinstance(currents, (int, float)):
            currents = [float(currents)]

        frequency = data.get('frequency', []) or data.get('freq', [])
        if isinstance(frequency, (int, float)):
            frequency = [float(frequency)]

        power = data.get('power', []) or data.get('pwr', [])
        if isinstance(power, (int, float)):
            power = [float(power)]

        power_factor = data.get('power_factor', []) or data.get('pf', [])
        if isinstance(power_factor, (int, float)):
            power_factor = [float(power_factor)]

        # Update in-memory data
        device_telemetry_data[device_id].update({
            'voltages': voltages,
            'currents': currents,
            'frequency': frequency,
            'power': power,
            'power_factor': power_factor,
            'timestamp': str(datetime.datetime.now(datetime.timezone.utc)),
            'device_id': device_id,
            'isConnected': True
        })

        # Prepare telemetry data
        telemetry_data = {
            'voltages': voltages,
            'currents': currents,
            'frequency': frequency,
            'power': power,
            'power_factor': power_factor
        }

        # Add to buffer for periodic storage
        if device_id not in telemetry_buffer:
            telemetry_buffer[device_id] = []

        telemetry_buffer[device_id].append(telemetry_data)

        # Calculate time until next storage
        current_time = datetime.datetime.now().timestamp()
        last_time = last_storage_time.get(device_id, 0)
        seconds_until_next_storage = max(0, 20 - (current_time - last_time))

        return jsonify({
            'success': True,
            'message': f'Test telemetry data added for device {device_id}',
            'data': device_telemetry_data[device_id],
            'buffered': True,
            'seconds_until_next_storage': seconds_until_next_storage
        })

    except Exception as e:
        logger.error(f"Error adding test telemetry: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

async def main():
    logger.info("IoT Hub Telemetry Monitor Starting...")

    try:
        env_vars = load_env_variables()

        # Create EventHub client with custom consumer group
        client = EventHubConsumerClient.from_connection_string(
            env_vars['EVENTHUB_CONNECTION_STRING'],
            consumer_group=env_vars['CONSUMER_GROUP']  # Use custom consumer group
        )

        # Start the periodic storage task
        logger.info("Starting periodic storage task...")
        asyncio.create_task(periodic_storage_task())

        logger.info("Starting to monitor telemetry events...")
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
    # Run the Flask app in a separate thread

    def run_app():
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True  # Allow main thread to exit even if app_thread is running
    app_thread.start()

    # Run the main async loop
    asyncio.run(main())


