import asyncio
import json
import os
import logging
import datetime
import time
import sys
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

# Dictionary to store background tasks for each device
device_tasks = {}

# Inactivity timeout in seconds (default: 1 hour)
INACTIVITY_TIMEOUT = int(os.getenv('INACTIVITY_TIMEOUT', 3600))

# Data staleness timeout in seconds (default: 5 minutes)
DATA_STALENESS_TIMEOUT = int(os.getenv('DATA_STALENESS_TIMEOUT', 300))

# API key for authentication (default: a secure 20-digit alphanumeric key)
API_KEY = os.getenv('API_KEY', 'Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1')

# Add this constant at the top with other constants
DEVICE_OFFLINE_TIMEOUT = 10  # seconds to wait before considering device offline

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
        'EVENTHUB_CONNECTION_STRING'
    ]

    env_vars = {var: os.getenv(var) for var in required_vars}
    missing_vars = [var for var in required_vars if not env_vars[var]]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Validate connection string
    if not validate_connection_string(env_vars['EVENTHUB_CONNECTION_STRING']):
        raise ValueError("Invalid Event Hub connection string format")

    # Hard-code the consumer group value
    env_vars['CONSUMER_GROUP'] = '$Default'

    return env_vars

async def create_eventhub_client(device_id):
    """Create an EventHub client for a specific device"""
    try:
        env_vars = load_env_variables()

        # Log connection details for debugging
        conn_string = env_vars['EVENTHUB_CONNECTION_STRING']
        # Extract and log the endpoint URL
        endpoint = next((part.split('=', 1)[1] for part in conn_string.split(';') if part.startswith('Endpoint=')), 'Unknown')
        entity_path = next((part.split('=', 1)[1] for part in conn_string.split(';') if part.startswith('EntityPath=')), 'Unknown')

        logger.info(f"Connecting to EventHub with endpoint: {endpoint}")
        logger.info(f"Using EntityPath: {entity_path}")
        logger.info(f"Using consumer group: {env_vars['CONSUMER_GROUP']}")

        # Create EventHub client with custom consumer group
        client = EventHubConsumerClient.from_connection_string(
            conn_string,
            consumer_group=env_vars['CONSUMER_GROUP']
        )

        logger.info(f"Created EventHub client for device: {device_id}")
        return client
    except Exception as e:
        logger.error(f"Error creating EventHub client for device {device_id}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        if hasattr(e, '__cause__') and e.__cause__:
            logger.error(f"Caused by: {e.__cause__}")
        raise

async def process_event(partition_context, event):
    """Handler for IoT Hub events"""
    try:
        device_id = event.system_properties.get(b'iothub-connection-device-id')
        if device_id:
            device_id = device_id.decode()
            telemetry_data = json.loads(event.body_as_str())
            # If telemetry_data does not contain 'power_factor', it won't be added to device_telemetry
            logger.info(f"Telemetry from {device_id}: {telemetry_data}")

            # Update telemetry data for this device
            global device_telemetry
            if device_id not in device_telemetry:
                device_telemetry[device_id] = {}

            # Update the data with current timestamp and connection status
            current_time = time.time()
            device_telemetry[device_id] = {
                **telemetry_data,
                'power_factor': telemetry_data.get('power_factor', []),  # Add default
                'timestamp': str(datetime.datetime.now(datetime.timezone.utc)),
                'isConnected': True,
                'last_data_received': current_time
            }

    except Exception as e:
        logger.error(f"Error processing event: {e}")

def is_data_stale(timestamp_str):
    """Check if data is stale based on timestamp"""
    if not timestamp_str:
        return True

    try:
        # Parse the timestamp
        if '+' in timestamp_str or 'Z' in timestamp_str:
            # Timestamp has timezone info
            timestamp = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            # Timestamp doesn't have timezone info, assume UTC
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)

        # Get current time in UTC
        now = datetime.datetime.now(datetime.timezone.utc)

        # Calculate time difference in seconds
        time_diff = (now - timestamp).total_seconds()

        # Return True if data is older than DATA_STALENESS_TIMEOUT
        return time_diff > DATA_STALENESS_TIMEOUT
    except Exception as e:
        logger.error(f"Error checking data staleness: {e}")
        return True  # Assume data is stale if we can't parse the timestamp

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

    # Use real data from Azure IoT Hub for the specified device
    if device_id in device_telemetry:
        device_data = device_telemetry[device_id]
        logger.info(f"Device telemetry for {device_id}: {device_data}")
        current_time = time.time()
        last_data_received = device_data.get('last_data_received', 0)

        # Check if device is offline based on last data received
        time_since_last_data = current_time - last_data_received
        is_device_offline = time_since_last_data > DEVICE_OFFLINE_TIMEOUT

        if is_device_offline:
            return jsonify({
                'deviceId': device_id,
                'voltages': [],
                'currents': [],
                'power': [],
                'frequency': [],
                'power_factor': [],
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'isConnected': False,
                'message': f'Device offline for {int(time_since_last_data)} seconds'
            })

        # Only return data if device is online
        telemetry = {
            'deviceId': device_id,
            'voltages': device_data.get('voltages', []),
            'currents': device_data.get('currents', []),
            'power': device_data.get('power', []),
            'frequency': device_data.get('frequency', []),
            'power_factor': device_data.get('power_factor', []),
            'timestamp': device_data.get('timestamp'),
            'isConnected': True
        }
    else:
        # Device not found or never connected
        telemetry = {
            'deviceId': device_id,
            'voltages': [],
            'currents': [],
            'power': [],
            'frequency': [],
            'power_factor': [],
            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'isConnected': False,
            'message': 'Device not registered or no data available'
        }

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

    # Flush older data for the device
    device_telemetry[device_id] = {
        'voltages': [],
        'currents': [],
        'power': [],
        'frequency': [],
        'power_factor': [],
        'timestamp': None,
        'isConnected': False
    }

    # Start monitoring the device
    asyncio.create_task(start_device_monitoring(device_id))

    # Wait for a short period to verify if the device starts sending data
    async def verify_device():
        await asyncio.sleep(DEVICE_OFFLINE_TIMEOUT)  # Wait for the timeout period
        if device_telemetry[device_id].get('last_data_received') is None:
            # No data received, mark the device as disconnected
            device_telemetry[device_id]['isConnected'] = False
            registered_devices[device_id]['status'] = 'disconnected'
            logger.warning(f"Device {device_id} did not send data within the timeout period. Marking as disconnected.")
        else:
            # Data received, mark the device as connected
            registered_devices[device_id]['status'] = 'connected'
            logger.info(f"Device {device_id} is actively sending data.")

    asyncio.create_task(verify_device())

    logger.info(f"Device registration initiated: {device_id}")
    return jsonify({
        'deviceId': device_id,
        'status': 'registering',
        'message': 'Device registration initiated'
    })

async def start_device_monitoring(device_id):
    """Start monitoring telemetry for a specific device"""
    try:
        # Check if device_id is valid
        if device_id not in registered_devices:
            logger.error(f"Attempted to monitor unregistered device: {device_id}")
            return False

        logger.info(f"Starting real-time monitoring for device {device_id}")
        logger.info(f"Creating EventHub client for device {device_id}")

        # Create EventHub client for this device
        client = await create_eventhub_client(device_id)

        # Store the client in the global dictionary
        device_clients[device_id] = client

        # Update device status
        registered_devices[device_id]['status'] = 'registered'
        logger.info(f"Device {device_id} registered successfully")

        # Start receiving events
        async def receive_events():
            try:
                logger.info(f"Starting to receive events for device {device_id}")
                async with client:
                    logger.info(f"Client context established for device {device_id}")
                    logger.info(f"Calling client.receive() for device {device_id}")
                    await client.receive(
                        on_event=process_event,
                        starting_position="-1"  # Start from end of stream
                    )
            except Exception as e:
                logger.error(f"Error receiving events for device {device_id}: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception details: {str(e)}")
                if hasattr(e, '__cause__') and e.__cause__:
                    logger.error(f"Caused by: {e.__cause__}")
                if device_id in registered_devices:
                    registered_devices[device_id]['status'] = 'error'

        # Create background task
        logger.info(f"Creating background task for device {device_id}")
        task = asyncio.create_task(receive_events())
        device_tasks[device_id] = task

        logger.info(f"Started monitoring for device: {device_id}")
        return True

    except Exception as e:
        logger.error(f"Error starting monitoring for device {device_id}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        if hasattr(e, '__cause__') and e.__cause__:
            logger.error(f"Caused by: {e.__cause__}")
        return False

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

async def check_connection_status():
    """Check connection status for all devices and attempt reconnection if needed"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            current_time = time.time()
            
            for device_id in list(device_telemetry.keys()):  # Create a copy of keys to iterate
                if device_id not in registered_devices:
                    logger.warning(f"Removing unregistered device from telemetry: {device_id}")
                    device_telemetry.pop(device_id, None)
                    continue

                last_received = device_telemetry[device_id].get('last_data_received', 0)
                time_diff = current_time - last_received
                
                if time_diff > DATA_STALENESS_TIMEOUT:
                    logger.error(f"No data received for {time_diff} seconds. Attempting reconnection for device {device_id}")
                    
                    # Stop existing client
                    if device_id in device_clients:
                        await stop_device_monitoring(device_id)
                    
                    # Restart client connection
                    success = await start_device_monitoring(device_id)
                    if success:
                        logger.info(f"Successfully reconnected device {device_id}")
                    else:
                        logger.error(f"Failed to reconnect device {device_id}")
                        # Don't exit, just continue monitoring other devices
                        
        except Exception as e:
            logger.error(f"Error in connection check: {e}")
            await asyncio.sleep(5)  # Wait a bit before retrying

# Add this new function to periodically check device status
async def check_device_status():
    """Periodically check device status and update connection state"""
    while True:
        try:
            current_time = time.time()
            for device_id in device_telemetry:
                last_received = device_telemetry[device_id].get('last_data_received', 0)
                if current_time - last_received > DEVICE_OFFLINE_TIMEOUT:
                    device_telemetry[device_id]['isConnected'] = False
                    device_telemetry[device_id]['voltages'] = []
                    device_telemetry[device_id]['currents'] = []
                    device_telemetry[device_id]['power'] = []
                    device_telemetry[device_id]['frequency'] = []
                    device_telemetry[device_id]['power_factor'] = []
            await asyncio.sleep(5)  # Check every 5 seconds
        except Exception as e:
            logger.error(f"Error in check_device_status: {e}")
            await asyncio.sleep(5)

async def main():
    try:
        # Start device status checker
        asyncio.create_task(check_device_status())
        
        # Start connection checker
        asyncio.create_task(check_connection_status())
        
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
                    'power': [],
                    'frequency': [],
                    'power_factor': [],
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
                await asyncio.sleep(60)
                
                # Update lastSeen for connected devices
                for device_id in list(device_telemetry.keys()):
                    if device_telemetry[device_id].get('isConnected', False):
                        if device_id in registered_devices:
                            registered_devices[device_id]['lastSeen'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

                # Check for inactive devices every 5 minutes
                if int(datetime.datetime.now().timestamp()) % 300 < 60:
                    logger.info("Checking for inactive devices...")
                    await check_inactive_devices()
                    
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
                
    except KeyboardInterrupt:
        logger.info("\nStopping telemetry monitor...")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

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
