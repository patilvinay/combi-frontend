# IoT Device Dashboard

A modern React dashboard for visualizing voltage and current telemetry data from Azure IoT Hub devices.

## Features

- Real-time voltage and current monitoring
- Interactive line charts using Recharts
- Dark theme with Material-UI components
- Automatic data refresh every 5 seconds
- Responsive design for all screen sizes

## Prerequisites

- Node.js 16.x or higher
- npm 8.x or higher
- Azure IoT Hub connection string (from parent directory's `.env` file)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.template .env
```

3. Copy the IoT Hub credentials from the parent directory's `.env` file:
```bash
VITE_EVENTHUB_CONNECTION_STRING=<copy from ../env EVENTHUB_CONNECTION_STRING>
VITE_CONSUMER_GROUP=<copy from ../env CONSUMER_GROUP>
VITE_DEVICE_ID=<copy from ../env DEVICE_ID>
```

## Development

Start the development server:
```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Building for Production

Build the dashboard:
```bash
npm run build
```

The built files will be in the `dist` directory.

## Integration with IoT Client

This dashboard works in conjunction with the IoT client in the parent directory. It:

1. Uses the same Event Hub connection string to access IoT Hub data
2. Displays real-time voltage and current readings from your IoT device
3. Updates automatically as new telemetry arrives

## Chart Components

1. **Voltage Chart**
   - Displays voltage readings over time
   - Y-axis: Voltage (V)
   - X-axis: Time points

2. **Current Chart**
   - Displays current readings over time
   - Y-axis: Current (A)
   - X-axis: Time points

3. **Latest Readings Panel**
   - Shows the most recent voltage and current values
   - Updates in real-time

## Technology Stack

- React 18 with TypeScript
- Material-UI for components
- Recharts for data visualization
- Azure Event Hubs SDK for IoT Hub integration
