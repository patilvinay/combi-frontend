#!/bin/bash

# Exit on any error
set -e

# Set environment variables
export DATABASE_URL=postgresql://iotuser:iotpassword@postgres:5432/iotdb
export API_KEY=Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1
export DEBUG=true

# Simple wait for PostgreSQL
echo "Waiting for PostgreSQL to be ready..."
sleep 10

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5050 --reload
