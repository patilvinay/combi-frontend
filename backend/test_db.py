#!/usr/bin/env python
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://iotuser:iotpassword@postgres:5432/iotdb')
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)