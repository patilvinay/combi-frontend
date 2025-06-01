# IoT Device Dashboard

A modern React dashboard for monitoring and managing IoT devices with real-time telemetry data visualization.

## ✨ Features

- **Device Management**: View, add, edit, and manage IoT devices
- **Real-time Monitoring**: Track device metrics and status in real-time
- **Responsive Design**: Fully responsive layout that works on all devices
- **Theme Support**: Light and dark mode with system preference detection
- **Modern UI**: Clean, accessible, and user-friendly interface
- **Secure**: API key authentication for all requests
- **Performance Optimized**: Efficient state management and data fetching
- **Docker Support**: Easy containerized deployment

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose (recommended)
- Node.js 18.x or higher (for development without Docker)
- npm 9.x or higher (for development without Docker)
- FastAPI backend service (included in Docker Compose)

### Quick Start with Docker Compose

The easiest way to run the application is using Docker Compose:

```bash
# Start all services (frontend, backend, and database)
docker compose up -d

# View logs
docker compose logs -f

# Access the application at http://localhost:3000
```

### Development Setup (Without Docker)

1. Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

2. Install dependencies and start the development server:

```bash
npm install
npm run dev
```

3. The application will be available at http://localhost:3000

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# API Configuration
VITE_API_URL=http://localhost:5050/api/v1
NODE_ENV=development

# Backend URL (used in development)
VITE_BACKEND_URL=http://localhost:5050
```

2. Configure the following environment variables in `.env`:

```env
REACT_APP_API_URL=http://localhost:5050/api/v1
REACT_APP_API_KEY=your-api-key-here
```

### Installation

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start the development server:

```bash
npm start
```

The application will be available at `http://localhost:3000`

## 🛠 Development

### Available Scripts

- `npm start`: Start the development server
- `npm test`: Run tests
- `npm run build`: Build for production
- `npm run eject`: Eject from Create React App

### Project Structure

```
frontend/
├── public/              # Static files
├── src/
│   ├── assets/         # Images, fonts, etc.
│   ├── components/      # Reusable UI components
│   ├── contexts/        # React context providers
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── services/        # API services
│   ├── styles/          # Global styles and themes
│   ├── utils/           # Utility functions
│   ├── App.js           # Main application component
│   └── index.js         # Application entry point
└── .env.example         # Example environment variables
```

## 🧪 Testing

Run the test suite:

```bash
npm test
```

## 🚀 Deployment

### Building for Production

```bash
npm run build
```

### Docker Deployment

Build and run using Docker:

```bash
docker-compose up --build
```

## 📚 Documentation

- [React Documentation](https://reactjs.org/)
- [React Router](https://reactrouter.com/)
- [Styled Components](https://styled-components.com/)
- [Axios](https://axios-http.com/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Create React App](https://create-react-app.dev/)
- [React Icons](https://react-icons.github.io/react-icons/)
- [React Toastify](https://fkhadra.github.io/react-toastify/)
- [Styled Components](https://styled-components.com/)
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
