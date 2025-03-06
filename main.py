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

    # Start Prometheus metrics server
    start_http_server(8000)  # Exposes metrics at http://localhost:8000/metrics
    SYSTEM_UPTIME.set(time.time())  # Set system start time

    # Read environment variables for MLLP and pager addresses
    mllp_address = os.getenv("MLLP_ADDRESS", "message-simulator:8440")
    pager_address = os.getenv("PAGER_ADDRESS", "message-simulator:8441")

    parser = HL7Parser()
    
    database = MySQLDatabase(
    host=os.getenv("MYSQL_HOST", "db"),
    port=os.getenv("MYSQL_PORT", "3306"),
    user=os.getenv("MYSQL_USER", "user"),
    password=os.getenv("MYSQL_PASSWORD", "password"),
    db=os.getenv("MYSQL_DB", "hospital_db")
        )
    database.connect()
    
    db_populator = DatabasePopulator(
        db=os.getenv("MYSQL_DB", "hospital_db"), 
        history_file="data/history.csv",  # Adjust the file path as needed for Kubernetes
        user=os.getenv("MYSQL_USER", "user"), 
        password=os.getenv("MYSQL_PASSWORD", "password"),
        host=os.getenv("MYSQL_HOST", "db"),
        port=os.getenv("MYSQL_PORT", "3306") 
    )
    db_populator.populate()
    
    pager = Pager(pager_address)
    model = Model()
    data_operator = DataOperator(database, model, pager)
    
    # Create the MLLP Listener instance
    mllp_listener = MllpListener(mllp_address, parser, data_operator)
    status = 0
    # ---------------------------------------------------- #
    # Running the system
    # ---------------------------------------------------- #
    while True:
        try:
            
            status = mllp_listener.run()
            if status == 1:
                logging.error(f"main.py: [ERROR] Database error occurred. Restarting MLLP listener when the database is available...")
                database.connect(delay=3)
                mllp_listener.open_connection()
                
        except Exception as e:
            logging.error(f"main.py: [ERROR] Exception occurred in MLLP listener: {e}")
            logging.info("main.py: [*] Restarting MLLP listener in 5 seconds...")
            time.sleep(5)  # Wait before restarting

    # ---------------------------------------------------- #
    # Shutdown stage
    # ---------------------------------------------------- #
    mllp_listener.shutdown() #This will never trigger


if __name__ == "__main__":
    main()
