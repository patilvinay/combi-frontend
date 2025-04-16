import asyncio
import json
import os
import logging
import datetime
from dotenv import load_dotenv
from azure.eventhub.aio import EventHubConsumerClient
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "DELETE"], "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]}})

# Authentication middleware
def require_api_key(f):
    """Decorator to require API key for routes"""
    def decorated(*args, **kwargs):
        # Check if API key is provided in header or query parameter
        provided_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        # If no API key is required, skip authentication
        if not API_KEY:
            return f(*args, **kwargs)

        # If API key is required but not provided or incorrect, return 401
        if not provided_key or provided_key != API_KEY:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid API key is required'
            }), 401

        return f(*args, **kwargs)

    # Preserve the original function's name and docstring
    decorated.__name__ = f.__name__
    decorated.__doc__ = f.__doc__

    return decorated

# Global dictionary to store the latest telemetry data for each device
device_telemetry = {}

# Default device ID from environment variable
DEFAULT_DEVICE_ID = None

# Dictionary to track registered devices
registered_devices = {}

# Dictionary to store EventHub clients for each device
device_clients = {}

# Dictionary to track when each device was last queried
last_queried = {}

# Inactivity timeout in seconds (default: 1 hour)
INACTIVITY_TIMEOUT = int(os.getenv('INACTIVITY_TIMEOUT', 3600))

# API key for authentication (default: a secure 20-digit alphanumeric key)
API_KEY = os.getenv('API_KEY', 'Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1')

# Flag to use mock data
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'

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
        'CONSUMER_GROUP'
    ]

    env_vars = {var: os.getenv(var) for var in required_vars}
    missing_vars = [var for var in required_vars if not env_vars[var]]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Validate connection string
    if not validate_connection_string(env_vars['EVENTHUB_CONNECTION_STRING']):
        raise ValueError("Invalid Event Hub connection string format")

    return env_vars

async def create_eventhub_client(device_id):
    """Create an EventHub client for a specific device"""
    try:
        env_vars = load_env_variables()

        # Create EventHub client with custom consumer group
        client = EventHubConsumerClient.from_connection_string(
            env_vars['EVENTHUB_CONNECTION_STRING'],
            consumer_group=env_vars['CONSUMER_GROUP']
        )

        logger.info(f"Created EventHub client for device: {device_id}")
        return client
    except Exception as e:
        logger.error(f"Error creating EventHub client for device {device_id}: {e}")
        raise

async def process_event(partition_context, event):
    """Handler for IoT Hub events"""
    try:
        device_id = event.system_properties.get(b'iothub-connection-device-id')
        if device_id:
            device_id = device_id.decode()
            telemetry_data = json.loads(event.body_as_str())
            logger.info(f"Telemetry from {device_id}: {telemetry_data}")

            # Update telemetry data for this device
            global device_telemetry
            if device_id not in device_telemetry:
                device_telemetry[device_id] = {}

            device_telemetry[device_id] = telemetry_data
            device_telemetry[device_id]['timestamp'] = str(datetime.datetime.now(datetime.timezone.utc))
            device_telemetry[device_id]['isConnected'] = True

    except Exception as e:
        logger.error(f"Error processing event: {e}")

@app.route('/api/telemetry')
@require_api_key
def get_telemetry():
    """REST endpoint to serve the latest telemetry data"""
    global last_queried

    # Get device ID from query parameter, or use default if not provided
    device_id = request.args.get('deviceId', DEFAULT_DEVICE_ID)

    if not device_id:
        return jsonify({'error': 'No device ID provided and no default device set'}), 400

    # Update the last queried timestamp for this device
    last_queried[device_id] = datetime.datetime.now(datetime.timezone.utc)

    if USE_MOCK_DATA:
        # Generate mock data for testing
        import random

        # Generate 6 random voltage and current values
        voltages = [round(random.uniform(220, 240), 1) for _ in range(6)]
        currents = [round(random.uniform(0.5, 5.0), 1) for _ in range(6)]

        telemetry = {
            'deviceId': device_id,
            'voltages': voltages,
            'currents': currents,
            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'isConnected': True
        }
    else:
        # Use real data from Azure IoT Hub for the specified device
        if device_id in device_telemetry:
            device_data = device_telemetry[device_id]
            telemetry = {
                'deviceId': device_id,
                'voltages': device_data.get('voltages', []),
                'currents': device_data.get('currents', []),
                'timestamp': device_data.get('timestamp'),
                'isConnected': device_data.get('isConnected', False)
            }
        else:
            # Device not found, return empty data
            telemetry = {
                'deviceId': device_id,
                'voltages': [],
                'currents': [],
                'timestamp': None,
                'isConnected': False,
                'message': 'Device not registered or no data available'
            }

    logger.info(f"Sending telemetry data for device {device_id}: {telemetry}")
    return jsonify(telemetry)

@app.route('/api/register-device', methods=['POST'])
@require_api_key
def register_device():
    """Register a device to start receiving telemetry"""
    global registered_devices, DEFAULT_DEVICE_ID, device_clients, last_queried

    data = request.json

    if not data or 'deviceId' not in data:
        return jsonify({'error': 'Device ID is required'}), 400

    device_id = data['deviceId']

    # Check if device is already registered
    if device_id in registered_devices:
        return jsonify({
            'deviceId': device_id,
            'status': 'already_registered',
            'message': 'Device is already registered'
        })

    # Get current time
    now = datetime.datetime.now(datetime.timezone.utc)

    # Store device information
    registered_devices[device_id] = {
        'registeredAt': now.isoformat(),
        'lastSeen': None,
        'status': 'registering'
    }

    # Initialize last queried timestamp
    last_queried[device_id] = now

    # If this is the first device, set it as the default
    if DEFAULT_DEVICE_ID is None:
        DEFAULT_DEVICE_ID = device_id

    # Initialize empty telemetry data for this device
    if device_id not in device_telemetry:
        device_telemetry[device_id] = {
            'voltages': [],
            'currents': [],
            'timestamp': None,
            'isConnected': False
        }

    # We can't use asyncio.create_task here because we're in a synchronous context
    # Instead, we'll just mark the device as registered and let the main loop handle it
    registered_devices[device_id]['status'] = 'registered'

    logger.info(f"Device registration initiated: {device_id}")
    return jsonify({
        'deviceId': device_id,
        'status': 'registering',
        'message': 'Device registration initiated'
    })

async def start_device_monitoring(device_id):
    """Start monitoring telemetry for a specific device"""
    try:
        if USE_MOCK_DATA:
            logger.info(f"Mock mode: Not creating real EventHub client for device {device_id}")
            registered_devices[device_id]['status'] = 'registered'
            return

        # Create EventHub client for this device
        client = await create_eventhub_client(device_id)

        # Store the client in the global dictionary
        device_clients[device_id] = client

        # Update device status
        registered_devices[device_id]['status'] = 'registered'

        # Start receiving events
        async def receive_events():
            try:
                async with client:
                    await client.receive(
                        on_event=process_event,
                        starting_position="-1"  # Start from end of stream
                    )
            except Exception as e:
                logger.error(f"Error receiving events for device {device_id}: {e}")
                registered_devices[device_id]['status'] = 'error'

        # Start the receive task in the background
        asyncio.create_task(receive_events())

        logger.info(f"Started monitoring for device: {device_id}")
    except Exception as e:
        logger.error(f"Error starting monitoring for device {device_id}: {e}")
        registered_devices[device_id]['status'] = 'error'

async def stop_device_monitoring(device_id):
    """Stop monitoring telemetry for a specific device"""
    try:
        if device_id in device_clients:
            client = device_clients.pop(device_id)
            # Close the client if it's still open
            try:
                await client.close()
                logger.info(f"Closed EventHub client for device: {device_id}")
            except Exception as e:
                logger.error(f"Error closing EventHub client for device {device_id}: {e}")

            # Update device status
            if device_id in registered_devices:
                registered_devices[device_id]['status'] = 'inactive'

            logger.info(f"Stopped monitoring for device: {device_id}")
    except Exception as e:
        logger.error(f"Error stopping monitoring for device {device_id}: {e}")

async def check_inactive_devices():
    """Check for inactive devices and stop their IoT Hub clients"""
    now = datetime.datetime.now(datetime.timezone.utc)
    inactive_devices = []

    # Find devices that haven't been queried for a while
    for device_id in list(device_clients.keys()):
        last_query_time = last_queried.get(device_id)
        if last_query_time is None:
            # If the device has never been queried, use its registration time
            if device_id in registered_devices:
                last_query_time = datetime.datetime.fromisoformat(registered_devices[device_id]['registeredAt'])
            else:
                # If we can't determine when it was last queried, consider it inactive
                inactive_devices.append(device_id)
                continue

        # Check if the device has been inactive for too long
        if (now - last_query_time).total_seconds() > INACTIVITY_TIMEOUT:
            inactive_devices.append(device_id)

    # Stop monitoring for inactive devices
    for device_id in inactive_devices:
        logger.info(f"Device {device_id} has been inactive for more than {INACTIVITY_TIMEOUT} seconds, stopping monitoring")
        await stop_device_monitoring(device_id)

@app.route('/api/devices', methods=['GET'])
@require_api_key
def get_devices():
    """Get a list of all registered devices"""
    devices = []

    for device_id, info in registered_devices.items():
        device_info = {
            'deviceId': device_id,
            'registeredAt': info['registeredAt'],
            'lastSeen': info['lastSeen'],
            'status': info.get('status', 'unknown'),
            'isConnected': device_id in device_telemetry and device_telemetry[device_id].get('isConnected', False)
        }
        devices.append(device_info)

    return jsonify({
        'devices': devices,
        'defaultDevice': DEFAULT_DEVICE_ID
    })

@app.route('/api/unregister-device/<device_id>', methods=['DELETE'])
@require_api_key
def unregister_device(device_id):
    """Unregister a device and stop receiving telemetry"""
    global DEFAULT_DEVICE_ID, registered_devices, device_clients, device_telemetry, last_queried

    if device_id not in registered_devices:
        return jsonify({
            'error': 'Device not found',
            'deviceId': device_id
        }), 404

    # Stop the EventHub client if it exists
    if device_id in device_clients:
        # Note: We can't actually stop the client here because it's running in an async context
        # and this is a synchronous endpoint. We'll just remove it from the dictionary and let
        # the background task handle cleanup.
        logger.info(f"Removing EventHub client for device: {device_id}")
        device_clients.pop(device_id, None)

    # Remove device from registered devices
    registered_devices.pop(device_id, None)

    # Remove device telemetry data
    device_telemetry.pop(device_id, None)

    # Remove device from last_queried
    last_queried.pop(device_id, None)

    # If this was the default device, set default to None
    if DEFAULT_DEVICE_ID == device_id:
        DEFAULT_DEVICE_ID = None
        # Set a new default if there are other devices
        if registered_devices:
            DEFAULT_DEVICE_ID = next(iter(registered_devices.keys()))

    logger.info(f"Device unregistered: {device_id}")
    return jsonify({
        'deviceId': device_id,
        'status': 'unregistered',
        'message': 'Device unregistered successfully'
    })

async def main():
    logger.info("IoT Hub Telemetry Monitor Starting...")

    # Initialize default device ID from environment variable
    global DEFAULT_DEVICE_ID
    DEFAULT_DEVICE_ID = os.getenv('DEVICE_ID')

    if DEFAULT_DEVICE_ID:
        logger.info(f"Default device ID set to: {DEFAULT_DEVICE_ID}")

        # Initialize empty telemetry data for the default device
        if DEFAULT_DEVICE_ID not in device_telemetry:
            device_telemetry[DEFAULT_DEVICE_ID] = {
                'voltages': [],
                'currents': [],
                'timestamp': None,
                'isConnected': False
            }

        # Register the default device
        registered_devices[DEFAULT_DEVICE_ID] = {
            'registeredAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'lastSeen': None,
            'status': 'registering'
        }

        # Start monitoring for the default device
        await start_device_monitoring(DEFAULT_DEVICE_ID)

    # Keep the application running
    while True:
        try:
            # Sleep to keep the async loop running
            await asyncio.sleep(60)

            # Update lastSeen for connected devices
            for device_id in list(device_telemetry.keys()):
                if device_telemetry[device_id].get('isConnected', False):
                    if device_id in registered_devices:
                        registered_devices[device_id]['lastSeen'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # Check for inactive devices every 5 minutes
            if int(datetime.datetime.now().timestamp()) % 300 < 60:  # Run every 5 minutes
                logger.info("Checking for inactive devices...")
                await check_inactive_devices()
        except KeyboardInterrupt:
            logger.info("\nStopping telemetry monitor...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    # Run the Flask app in a separate thread
    import threading

    # Install eventlet only when running in production
    if os.environ.get('FLASK_ENV') == 'production':
        import eventlet
        eventlet.monkey_patch()

    def run_app():
        # Run the Flask app with host='0.0.0.0' to make it accessible from other devices
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True  # Allow main thread to exit even if app_thread is running
    app_thread.start()

    # Run the main async loop
    asyncio.run(main())
