#!/usr/bin/python3

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo  # Python 3.9+
from sqlalchemy import create_engine, text

# Database connection URL (update if needed)
DATABASE_URL = "postgresql://iotuser:iotpassword@localhost:5432/iotdb"

# Table and timestamp column
TABLE_NAME = "measurements"
TIMESTAMP_COLUMN = "created_at"  # Change if your timestamp column is different

# Calculate cutoff datetime (7 days ago)
cutoff = datetime.now() - timedelta(days=7)

engine = create_engine(DATABASE_URL)
log_file_path = Path(__file__).with_name("deletion_log.txt")

with engine.begin() as conn:
    result = conn.execute(
        text(f"DELETE FROM {TABLE_NAME} WHERE {TIMESTAMP_COLUMN} < :cutoff"),
        {"cutoff": cutoff},
    )
    indian_time = datetime.now(ZoneInfo("Asia/Kolkata"))
    log_message = (
        f"{indian_time} (IST) - Deleted {result.rowcount} rows older than 7 days.\n"
    )
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(log_message)
