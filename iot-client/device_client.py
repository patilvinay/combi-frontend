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
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    day_number = Column(Integer)  # 1, 2, or 3 representing which day's data this is
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
    'timestamp': None,
    'device_id': None
})

# Dictionary to track the last time data was stored for each device
last_storage_time = {}

# Dictionary to buffer telemetry data between storage intervals
telemetry_buffer = {}

# Dictionary to track the start time of each day for each device
day_start_times = {}

# For testing: day duration in seconds (2 minutes = 120 seconds)
DAY_DURATION_SECONDS = 120  # Change to 86400 (24 hours) for production

# Create a background task to handle periodic storage
async def periodic_storage_task():
    """Background task to ensure data is stored every 5 seconds"""
    while True:
        try:
            current_time = datetime.datetime.now().timestamp()

            # Check each device's buffer
            for device_id, buffer in list(telemetry_buffer.items()):
                if not buffer:  # Skip empty buffers
                    continue

                last_time = last_storage_time.get(device_id, 0)

                # If 5 seconds have passed since last storage, store the data
                if current_time - last_time >= 5:
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

# Create a background task to periodically clean up invalid day numbers
async def cleanup_task():
    """Background task to ensure we only keep data for days 1, 2, and 3"""
    while True:
        try:
            logger.debug("Running cleanup task to check for invalid day numbers")

            db = SessionLocal()
            valid_days = [1, 2, 3]

            # Find all devices with data
            devices = db.query(TelemetryData.device_id).distinct().all()
            devices = [device[0] for device in devices]

            for device_id in devices:
                # Find invalid day numbers for this device
                invalid_days = db.query(TelemetryData.day_number).filter(
                    TelemetryData.device_id == device_id,
                    ~TelemetryData.day_number.in_(valid_days)
                ).distinct().all()

                if invalid_days:
                    invalid_day_numbers = [day[0] for day in invalid_days]
                    logger.warning(f"Cleanup task: Found data with invalid day numbers: {invalid_day_numbers} for device {device_id}")

                    # Delete all data with invalid day numbers
                    deleted_count = db.query(TelemetryData).filter(
                        TelemetryData.device_id == device_id,
                        ~TelemetryData.day_number.in_(valid_days)
                    ).delete()

                    logger.info(f"Cleanup task: Deleted {deleted_count} records with invalid day numbers for device {device_id}")
                    db.commit()

                # Also check if we have more than one record per day (we should only have the latest)
                for day_num in valid_days:
                    # Get all records for this day, ordered by timestamp (oldest first)
                    day_records = db.query(TelemetryData).filter(
                        TelemetryData.device_id == device_id,
                        TelemetryData.day_number == day_num
                    ).order_by(TelemetryData.timestamp).all()

                    # If we have more than one record, keep only the newest one
                    if len(day_records) > 1:
                        # Keep the newest record (last in the list)
                        newest_record = day_records[-1]

                        # Delete all older records
                        deleted_count = db.query(TelemetryData).filter(
                            TelemetryData.device_id == device_id,
                            TelemetryData.day_number == day_num,
                            TelemetryData.id != newest_record.id
                        ).delete()

                        logger.info(f"Cleanup task: Deleted {deleted_count} older records for day {day_num} (keeping only the newest)")
                        db.commit()

            db.close()

            # Run this task every minute
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Error in cleanup task: {e}", exc_info=True)
            await asyncio.sleep(60)  # Sleep for a minute on error

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
    """Manage continuous data storage with day tracking using accelerated time scale for testing"""
    try:
        db = SessionLocal()
        current_time = datetime.datetime.now(datetime.timezone.utc)
        current_timestamp = current_time.timestamp()

        # Initialize day tracking for this device if not already done
        if device_id not in day_start_times:
            day_start_times[device_id] = {
                'start_time': current_timestamp,
                'current_day': 1,
                'absolute_day': 1  # Track the absolute day number (never resets)
            }
            logger.info(f"Initialized day tracking for device {device_id}, starting day 1")

        # Check if we need to start a new day based on elapsed time
        day_info = day_start_times[device_id]
        elapsed_seconds = current_timestamp - day_info['start_time']
        days_elapsed = int(elapsed_seconds / DAY_DURATION_SECONDS)

        # If days have elapsed, update the day number
        if days_elapsed > 0:
            # Update the start time to the beginning of the current day
            day_info['start_time'] += days_elapsed * DAY_DURATION_SECONDS

            # Update the absolute day number (for tracking purposes)
            day_info['absolute_day'] += days_elapsed

            # Calculate the current day (1, 2, or 3) based on the absolute day
            # We use modulo to cycle through days 1, 2, 3
            current_day = ((day_info['absolute_day'] - 1) % 3) + 1

            logger.info(f"New day detected! Absolute day {day_info['absolute_day']}, using day {current_day} for device {device_id}")

            # If we're on day 4 or higher, we need to delete old data
            if day_info['absolute_day'] > 3:
                # Delete old data for the current day (which is being replaced)
                deleted_count = db.query(TelemetryData).filter(
                    TelemetryData.device_id == device_id,
                    TelemetryData.day_number == current_day
                ).delete()

                logger.info(f"Deleted {deleted_count} records for day {current_day} (replaced by absolute day {day_info['absolute_day']})")
        else:
            # Still the same day
            current_day = ((day_info['absolute_day'] - 1) % 3) + 1

        # IMPORTANT: Ensure we only have data for days 1, 2, and 3
        # This is a safety check to clean up any data that might have been stored with incorrect day numbers
        valid_days = [1, 2, 3]
        invalid_days = db.query(TelemetryData.day_number).filter(
            TelemetryData.device_id == device_id,
            ~TelemetryData.day_number.in_(valid_days)
        ).distinct().all()

        if invalid_days:
            invalid_day_numbers = [day[0] for day in invalid_days]
            logger.warning(f"Found data with invalid day numbers: {invalid_day_numbers} for device {device_id}. Cleaning up...")

            # Delete all data with invalid day numbers
            deleted_count = db.query(TelemetryData).filter(
                TelemetryData.device_id == device_id,
                ~TelemetryData.day_number.in_(valid_days)
            ).delete()

            logger.info(f"Deleted {deleted_count} records with invalid day numbers for device {device_id}")

        # Log the current day and time info
        time_until_next_day = DAY_DURATION_SECONDS - (elapsed_seconds % DAY_DURATION_SECONDS)
        logger.info(f"Using day number: {current_day} for device {device_id} (next day in {time_until_next_day:.1f} seconds)")

        # Insert new data
        new_telemetry = TelemetryData(
            device_id=device_id,
            voltages=telemetry_data.get('voltages', []),
            currents=telemetry_data.get('currents', []),
            frequency=telemetry_data.get('frequency', []),
            power=telemetry_data.get('power', []),
            timestamp=current_time,
            day_number=current_day,
            is_connected=True
        )
        db.add(new_telemetry)
        logger.info(f"Added new telemetry data for device {device_id} on day {current_day}")

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
            if not any(key in telemetry_data for key in ['voltages', 'currents', 'frequency', 'power']):
                logger.warning(f"Event does not contain expected telemetry fields. Event data: {telemetry_data}")

                # Try to extract data from different formats
                # Format 1: Single values instead of arrays
                voltages = []
                currents = []
                frequency = []
                power = []

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

                # Update with the extracted values
                device_telemetry_data[decoded_device_id].update({
                    'voltages': voltages,
                    'currents': currents,
                    'frequency': frequency,
                    'power': power,
                    'timestamp': str(datetime.datetime.now(datetime.timezone.utc)),
                    'device_id': decoded_device_id,
                    'isConnected': True
                })

                # Create a compatible format for database storage
                compatible_telemetry = {
                    'voltages': voltages,
                    'currents': currents,
                    'frequency': frequency,
                    'power': power
                }

                # Add to buffer for periodic storage
                if decoded_device_id not in telemetry_buffer:
                    telemetry_buffer[decoded_device_id] = []

                telemetry_buffer[decoded_device_id].append(compatible_telemetry)
                logger.debug(f"Added data to buffer for device {decoded_device_id} (will be stored on next 5-second interval)")

            else:
                # Original format with arrays
                logger.info(f"Processing standard format telemetry data")

                # Store in memory (for immediate access)
                device_telemetry_data[decoded_device_id].update({
                    'voltages': telemetry_data.get('voltages', []),
                    'currents': telemetry_data.get('currents', []),
                    'frequency': telemetry_data.get('frequency', []),
                    'power': telemetry_data.get('power', []),
                    'timestamp': str(datetime.datetime.now(datetime.timezone.utc)),
                    'device_id': decoded_device_id,
                    'isConnected': True
                })

                # Add to buffer for periodic storage
                if decoded_device_id not in telemetry_buffer:
                    telemetry_buffer[decoded_device_id] = []

                telemetry_buffer[decoded_device_id].append(telemetry_data)
                logger.debug(f"Added data to buffer for device {decoded_device_id} (will be stored on next 5-second interval)")

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

        # Get the current day number for this device
        latest_record = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id
        ).order_by(TelemetryData.timestamp.desc()).first()

        if not latest_record:
            return jsonify({
                'error': f"No data found for device {device_id}",
                'available_devices': []
            }), 404

        current_day = latest_record.day_number
        logger.info(f"Current day for device {device_id} is {current_day}")

        # Get all records for the current day
        current_day_records = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id,
            TelemetryData.day_number == current_day
        ).order_by(TelemetryData.timestamp.desc()).all()

        # Combine all data points for the current day
        voltages = []
        currents = []
        frequency = []
        power = []

        for record in current_day_records:
            if record.voltages:
                voltages.extend(record.voltages)
            if record.currents:
                currents.extend(record.currents)
            if record.frequency:
                frequency.extend(record.frequency)
            if record.power:
                power.extend(record.power)

        # Get the total number of days we have data for
        total_days = db.query(TelemetryData.day_number).filter(
            TelemetryData.device_id == device_id
        ).distinct().count()

        # Prepare the response with the current day's data
        response_data = {
            'voltages': voltages,
            'currents': currents,
            'frequency': frequency,
            'power': power,
            'timestamp': str(latest_record.timestamp),
            'isConnected': latest_record.is_connected,
            'device_id': device_id,
            'day_number': current_day,
            'total_days': total_days
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

        # Get all records for this device, ordered by day number
        all_records = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id
        ).order_by(TelemetryData.day_number).all()

        if not all_records:
            return jsonify({
                'error': f"No data found for device {device_id}",
                'available_devices': []
            }), 404

        # Format all days' data
        days_data = []
        for record in all_records:
            days_data.append({
                'voltages': record.voltages or [],
                'currents': record.currents or [],
                'frequency': record.frequency or [],
                'power': record.power or [],
                'timestamp': str(record.timestamp),
                'isConnected': record.is_connected,
                'device_id': device_id,
                'day_number': record.day_number
            })

        return jsonify({
            'device_id': device_id,
            'days': days_data,
            'total_days': len(days_data)
        })

    except Exception as e:
        logger.error(f"Error retrieving telemetry: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()

@app.route('/api/telemetry/<device_id>/day/<int:day_number>')
def get_device_telemetry_by_day(device_id, day_number):
    """REST endpoint to serve telemetry data for a specific device and day"""
    try:
        db = SessionLocal()

        # Get data for the specified day
        telemetry_data = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id,
            TelemetryData.day_number == day_number
        ).first()

        if telemetry_data:
            # Return the specified day's data
            response_data = {
                'voltages': telemetry_data.voltages or [],
                'currents': telemetry_data.currents or [],
                'frequency': telemetry_data.frequency or [],
                'power': telemetry_data.power or [],
                'timestamp': str(telemetry_data.timestamp),
                'isConnected': telemetry_data.is_connected,
                'device_id': device_id,
                'day_number': day_number
            }

            return jsonify(response_data)
        else:
            return jsonify({
                'error': f"Device {device_id} not found for day {day_number}",
                'available_devices': []
            }), 404

    except Exception as e:
        logger.error(f"Error retrieving telemetry: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        db.close()

@app.route('/api/telemetry/<device_id>/day1')
def get_device_telemetry_day1(device_id):
    """REST endpoint to serve day 1 telemetry data for a specific device"""
    try:
        db = SessionLocal()

        # Get all records for day 1
        day1_records = db.query(TelemetryData).filter(
            TelemetryData.device_id == device_id,
            TelemetryData.day_number == 1
        ).order_by(TelemetryData.timestamp.desc()).all()

        if day1_records:
            # Combine all data points for day 1
            voltages = []
            currents = []
            frequency = []
            power = []

            for record in day1_records:
                if record.voltages:
                    voltages.extend(record.voltages)
                if record.currents:
                    currents.extend(record.currents)
                if record.frequency:
                    frequency.extend(record.frequency)
                if record.power:
                    power.extend(record.power)

            # Return day 1's combined data
            response_data = {
                'voltages': voltages,
                'currents': currents,
                'frequency': frequency,
                'power': power,
                'timestamp': str(day1_records[0].timestamp),
                'isConnected': day1_records[0].is_connected,
                'device_id': device_id,
                'day_number': 1
            }

            return jsonify(response_data)
        else:
            return jsonify({
                'error': f"Day 1 data not found for device {device_id}",
                'available_devices': []
            }), 404

    except Exception as e:
        logger.error(f"Error retrieving day 1 telemetry: {e}", exc_info=True)
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

        # Update in-memory data
        device_telemetry_data[device_id].update({
            'voltages': voltages,
            'currents': currents,
            'frequency': frequency,
            'power': power,
            'timestamp': str(datetime.datetime.now(datetime.timezone.utc)),
            'device_id': device_id,
            'isConnected': True
        })

        # Prepare telemetry data
        telemetry_data = {
            'voltages': voltages,
            'currents': currents,
            'frequency': frequency,
            'power': power
        }

        # Add to buffer for periodic storage
        if device_id not in telemetry_buffer:
            telemetry_buffer[device_id] = []

        telemetry_buffer[device_id].append(telemetry_data)

        # Calculate time until next storage
        current_time = datetime.datetime.now().timestamp()
        last_time = last_storage_time.get(device_id, 0)
        seconds_until_next_storage = max(0, 5 - (current_time - last_time))

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

        # Start the cleanup task
        logger.info("Starting cleanup task...")
        asyncio.create_task(cleanup_task())

        # Run an immediate cleanup to remove any invalid day numbers from previous runs
        logger.info("Running initial cleanup...")
        db = SessionLocal()
        valid_days = [1, 2, 3]

        # Find all devices with data
        devices = db.query(TelemetryData.device_id).distinct().all()
        devices = [device[0] for device in devices]

        for device_id in devices:
            # Find invalid day numbers for this device
            invalid_days = db.query(TelemetryData.day_number).filter(
                TelemetryData.device_id == device_id,
                ~TelemetryData.day_number.in_(valid_days)
            ).distinct().all()

            if invalid_days:
                invalid_day_numbers = [day[0] for day in invalid_days]
                logger.warning(f"Initial cleanup: Found data with invalid day numbers: {invalid_day_numbers} for device {device_id}")

                # Delete all data with invalid day numbers
                deleted_count = db.query(TelemetryData).filter(
                    TelemetryData.device_id == device_id,
                    ~TelemetryData.day_number.in_(valid_days)
                ).delete()

                logger.info(f"Initial cleanup: Deleted {deleted_count} records with invalid day numbers for device {device_id}")
                db.commit()

            # Also check if we have more than one record per day (we should only have the latest)
            for day_num in valid_days:
                # Get all records for this day, ordered by timestamp (oldest first)
                day_records = db.query(TelemetryData).filter(
                    TelemetryData.device_id == device_id,
                    TelemetryData.day_number == day_num
                ).order_by(TelemetryData.timestamp).all()

                # If we have more than one record, keep only the newest one
                if len(day_records) > 1:
                    # Keep the newest record (last in the list)
                    newest_record = day_records[-1]

                    # Delete all older records
                    deleted_count = db.query(TelemetryData).filter(
                        TelemetryData.device_id == device_id,
                        TelemetryData.day_number == day_num,
                        TelemetryData.id != newest_record.id
                    ).delete()

                    logger.info(f"Initial cleanup: Deleted {deleted_count} older records for day {day_num} (keeping only the newest)")
                    db.commit()

        db.close()
        logger.info("Initial cleanup complete")

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


