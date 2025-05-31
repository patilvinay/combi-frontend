# IoT Time Series Backend API

A high-performance FastAPI backend for collecting, storing, and querying time series data from IoT devices. This service provides a RESTful API for managing electrical measurements including voltage, current, power, frequency, and power factor across multiple phases.

## 📋 Features

- **Multi-phase Support**: Store and retrieve measurements for up to 7 phases per device
- **Time-based Queries**: Filter measurements by time ranges or get the most recent data
- **Scalable Architecture**: Built with FastAPI and SQLAlchemy for high performance
- **Containerized**: Easy deployment with Docker and Docker Compose
- **Health Monitoring**: Built-in health check endpoints
- **Comprehensive Documentation**: Interactive API docs with Swagger UI and ReDoc

## 🚀 Getting Started
## Running the Application

### Prerequisites
- Docker and Docker Compose

### Starting the services
```bash
docker-compose up -d
```

The API will be available at `http://localhost:5050`

### View API documentation
- Interactive API docs: http://localhost:5050/docs
- Alternative docs: http://localhost:5050/redoc
