# src/logger.py
from loguru import logger
import sqlite3
import uuid
from datetime import datetime
import os

# Create logs directory
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

def sqlite_log_handler(record):
    try:
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            message TEXT
        );
        ''')

        log_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level = record["level"].name
        message = record["message"]

        cursor.execute('''
        INSERT INTO logs (id, timestamp, level, message)
        VALUES (?, ?, ?, ?)
        ''', (log_id, timestamp, level, message))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error logging to SQLite: {str(e)}")

# This part is critical! Wrap the handler to access `.record`
logger.add(lambda msg: sqlite_log_handler(msg.record), level="INFO", enqueue=True)
logger.add("logs/app.log", rotation="1 week", level="INFO")
