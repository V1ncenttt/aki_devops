"""
Main System Module
==================
This module initializes and runs the HL7 message processing system, handling message reception, parsing,
prediction, and alerting mechanisms.

Usage:
------
Run this script to start the system:
    python main.py

"""

#!/usr/bin/env python3
"""
Main System Module
==================
This module initializes and runs the HL7 message processing system, handling message reception, parsing,
prediction, and alerting mechanisms.

Usage:
------
Run this script to start the system:
    python main.py
"""

import os
import time
import logging
import signal
from prometheus_client import start_http_server
from src.metrics import HL7_MESSAGES_RECEIVED, AKI_PAGES_SENT, AKI_PAGES_FAILED, PREDICTIONS_MADE, SYSTEM_UPTIME
from src.pandas_database import PandasDatabase
from src.mllp_listener import MllpListener
from src.model import Model
from src.data_operator import DataOperator
from src.pager import Pager
from src.mysql_database import MySQLDatabase
from src.parser import HL7Parser
from src.database_populator import DatabasePopulator

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    """
    Main function that initializes and runs the HL7 message processing system.
    """
    # Wait for dependent services to start
    time.sleep(60)
    
    # Start Prometheus metrics server
    start_http_server(8000)  # Exposes metrics at http://localhost:8000/metrics
    SYSTEM_UPTIME.set(time.time())  # Set system start time

    # Read environment variables for MLLP and pager addresses
    mllp_address = os.getenv("MLLP_ADDRESS", "message-simulator:8440")
    pager_address = os.getenv("PAGER_ADDRESS", "message-simulator:8441")

    parser = HL7Parser()
    
    db_populator = DatabasePopulator(
        db=os.getenv("MYSQL_DB", "hospital_db"), 
        history_file="data/history.csv",  # Adjust the file path as needed for Kubernetes
        user=os.getenv("MYSQL_USER", "user"), 
        password=os.getenv("MYSQL_PASSWORD", "password"),
        host=os.getenv("MYSQL_HOST", "db"),
        port=os.getenv("MYSQL_PORT", "3306") 
    )
    db_populator.populate()
    
    database = MySQLDatabase(
    host=os.getenv("MYSQL_HOST", "db"),
    port=os.getenv("MYSQL_PORT", "3306"),
    user=os.getenv("MYSQL_USER", "user"),
    password=os.getenv("MYSQL_PASSWORD", "password"),
    db=os.getenv("MYSQL_DB", "hospital_db")
    )
    database.connect()
    
    pager = Pager(pager_address)
    model = Model()
    data_operator = DataOperator(database, model, pager)
    
    # Create the MLLP Listener instance
    mllp_listener = MllpListener(mllp_address, parser, data_operator)

    # Register signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logging.info(f"main.py: Received signal {signum}. Initiating graceful shutdown...")
        mllp_listener.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signals

    # Run the listener continuously until shutdown is triggered
    try:
        while mllp_listener.running:
            mllp_listener.run()
    except Exception as e:
        logging.error(f"main.py: [ERROR] Exception occurred in MLLP listener: {e}")
        logging.info("main.py: [*] Restarting MLLP listener in 5 seconds...")
        time.sleep(5)
    finally:
        logging.info("main.py: Exiting main loop.")
    
if __name__ == "__main__":
    main()
