# IoT Client

## Overview
This client monitors real-time telemetry from specific devices in your Azure IoT Hub. It uses the Event Hub-compatible endpoint to receive device-to-cloud messages and filters them based on device ID.

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

# Device ID to monitor
DEVICE_ID=<your-device-id>
```

## Implementation Method

### 1. Connection Setup
- Uses Azure Event Hubs SDK to connect to IoT Hub's built-in endpoint
- Configures consumer group for message partitioning
- Validates connection string format and required environment variables

### 2. Message Processing
- Implements async event processing using `EventHubConsumerClient`
- Filters messages by device ID using system properties
- Parses JSON telemetry data from message body
- Logs formatted output with timestamp and device information

### 3. Error Handling
- Validates environment variables and connection strings
- Provides detailed error messages for connection issues
- Implements graceful error recovery and reconnection

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
