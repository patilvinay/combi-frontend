# IoT Client

## Overview
This client monitors real-time telemetry from specific devices in your Azure IoT Hub. It uses the Event Hub-compatible endpoint to receive device-to-cloud messages and filters them based on device ID. The client provides a REST API for registering devices, retrieving telemetry data, and managing device connections.

## Setup

1. Make sure you have Python 3 installed on your system:
```bash
python3 --version
```

2. (Optional) Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
.\venv\Scripts\activate  # On Windows
```

3. Install required dependencies:
```bash
pip3 install azure-eventhub python-dotenv
```

## Configuration

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Update `.env` with your IoT Hub details:
```plaintext
# Event Hub Connection String for IoT Hub's built-in endpoint
EVENTHUB_CONNECTION_STRING=<your-eventhub-compatible-connection-string>

# Event Hub Consumer Group (default: $Default)
CONSUMER_GROUP=$Default

# Default Device ID to monitor (optional)
DEVICE_ID=<your-device-id>

# Inactivity timeout in seconds (default: 3600 = 1 hour)
# INACTIVITY_TIMEOUT=3600

# API key for authentication (leave empty to disable authentication)
# API_KEY=Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1
```

## Implementation Method

### 1. Connection Setup
- Uses Azure Event Hubs SDK to connect to IoT Hub's built-in endpoint
- Configures consumer group for message partitioning
- Validates connection string format and required environment variables
- Creates separate EventHub clients for each registered device

### 2. Message Processing
- Implements async event processing using `EventHubConsumerClient`
- Filters messages by device ID using system properties
- Parses JSON telemetry data from message body
- Logs formatted output with timestamp and device information
- Stores telemetry data in memory for each device

### 3. REST API
- Implements a Flask-based REST API for device management and telemetry retrieval
- Provides endpoints for registering and unregistering devices
- Allows querying telemetry data for specific devices
- Returns data in JSON format for easy integration with other applications
- Includes API key authentication for securing endpoints

### 4. Resource Management
- Tracks when each device was last queried for telemetry data
- Automatically stops IoT Hub clients for devices that haven't been queried for a configurable period
- Ensures efficient use of resources by only maintaining connections for active devices

### 5. Error Handling
- Validates environment variables and connection strings
- Provides detailed error messages for connection issues
- Implements graceful error recovery and reconnection
- Handles errors in the REST API with appropriate HTTP status codes

## Running the Client

Start the monitoring client:
```bash
python3 device_client.py
```

The client will:
1. Connect to your IoT Hub's Event Hub endpoint
2. Listen for incoming device messages
3. Filter and display messages from your specified device
4. Log telemetry data in a readable format
5. Start a REST API server on port 5000

You can then interact with the REST API using tools like curl, Postman, or directly from your application:

```bash
# List all registered devices
curl -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" http://localhost:5000/api/devices

# Register a new device
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" -d '{"deviceId":"my-device-1"}' http://localhost:5000/api/register-device

# Get telemetry for a specific device
curl -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" http://localhost:5000/api/telemetry?deviceId=my-device-1

# Unregister a device
curl -X DELETE -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" http://localhost:5000/api/unregister-device/my-device-1
```

Note: Always use `python3` command explicitly instead of `python`.

## Logging
- Uses Python's built-in logging module
- Includes timestamp and log level
- Shows device ID and telemetry content
- Provides connection status updates

## Error Messages
- Missing environment variables
- Invalid connection string format
- Connection failures
- Message processing errors
- Authentication failures

## Authentication

The REST API is protected by API key authentication using a 20-digit alphanumeric client key. This provides a basic level of security to prevent unauthorized access to your IoT data and device management functions.

### Configuring the API Key

You can configure the API key in the `.env` file:

```plaintext
API_KEY=Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1
```

The default API key is `Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1`, but you should change this to your own secure key in production environments.

### Generating a Custom API Key

For better security, you should generate your own random API key. You can use Python to generate a secure random key:

```python
import secrets
import string

# Generate a 20-character alphanumeric key
characters = string.ascii_letters + string.digits
api_key = ''.join(secrets.choice(characters) for _ in range(20))
print(f"Your new API key: {api_key}")
```

### Using the API Key in Requests

To access the API endpoints, you need to include the API key in your requests using one of these methods:

1. **HTTP Header** (Recommended): Include the API key in the `X-API-Key` header:
   ```
   X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1
   ```

2. **Query Parameter**: Include the API key as a query parameter:
   ```
   ?api_key=Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1
   ```

### Examples with curl

```bash
# Using header (recommended)
curl -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" http://localhost:5000/api/devices

# Using query parameter
curl "http://localhost:5000/api/devices?api_key=Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1"
```

### Disabling Authentication

If you don't want to use authentication, you can disable it by setting an empty API_KEY in the environment variables:

```plaintext
API_KEY=
```

### Security Considerations

- The API key is transmitted in plain text, so it's recommended to use HTTPS in production environments
- Keep your API key secret and don't commit it to version control
- Regularly rotate your API key for better security
- The header method is preferred over query parameters as query parameters may be logged in server logs

## REST API

The client provides a REST API for interacting with devices and retrieving telemetry data. The API is built using Flask and provides the following endpoints. All endpoints require API key authentication as described in the Authentication section above.

### Device Registration and Management

#### Register a Device
```
POST /api/register-device
```
Request body:
```json
{
  "deviceId": "your-device-id"
}
```
Response:
```json
{
  "deviceId": "your-device-id",
  "status": "registering",
  "message": "Device registration initiated"
}
```

Example with curl:
```bash
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" \
  -d '{"deviceId":"your-device-id"}' \
  http://localhost:5000/api/register-device
```

#### Unregister a Device
```
DELETE /api/unregister-device/<device_id>
```
Response:
```json
{
  "deviceId": "your-device-id",
  "status": "unregistered",
  "message": "Device unregistered successfully"
}
```

Example with curl:
```bash
curl -X DELETE -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" \
  http://localhost:5000/api/unregister-device/your-device-id
```

#### List All Devices
```
GET /api/devices
```
Response:
```json
{
  "devices": [
    {
      "deviceId": "device-1",
      "registeredAt": "2023-04-13T18:25:47.126748+00:00",
      "lastSeen": "2023-04-13T18:29:47.224792+00:00",
      "status": "registered",
      "isConnected": true
    }
  ],
  "defaultDevice": "device-1"
}
```

Example with curl:
```bash
curl -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" \
  http://localhost:5000/api/devices
```

### Telemetry Data

#### Get Telemetry for a Device
```
GET /api/telemetry?deviceId=<device_id>
```
Response:
```json
{
  "deviceId": "your-device-id",
  "timestamp": "2023-04-13T18:29:47.224792+00:00",
  "isConnected": true,
  "voltages": [12.1, 12.2, 12.3],
  "currents": [1.1, 1.2, 1.3]
}
```

Example with curl:
```bash
curl -H "X-API-Key: Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1" \
  "http://localhost:5000/api/telemetry?deviceId=your-device-id"
```

## Resource Management

The client implements resource management to avoid wasting resources on inactive devices:

### Inactivity Tracking
- The client tracks when each device was last queried for telemetry data
- If a device hasn't been queried for more than 1 hour (configurable), its IoT Hub client is stopped
- This ensures that resources are only used for devices that are actively being monitored

### Device Monitoring
- When a device is registered, a new EventHub client is created for that device
- The client filters messages from the IoT Hub based on the device ID
- Telemetry data is stored in memory and made available through the REST API
- When a device is unregistered or becomes inactive, its EventHub client is stopped
