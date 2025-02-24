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
from prometheus_client import start_http_server, Counter, Gauge
from src.pandas_database import PandasDatabase
from src.mllp_listener import MllpListener
from src.model import Model
from src.data_operator import DataOperator
from src.pager import Pager
from src.parser import HL7Parser

# ------------------ Prometheus Metrics ------------------ #
hl7_messages_received = Counter('hl7_messages_received_total', 'Total number of HL7 messages received')
aki_pages_sent = Counter('aki_pages_sent_total', 'Total number of AKI event pages sent')
aki_pages_failed = Counter('aki_pages_failed_total', 'Total number of failed AKI event pages')
predictions_made = Counter('aki_predictions_total', 'Total number of AKI predictions made')
system_uptime = Gauge('system_uptime_seconds', 'Time since the system started')

def main():
    """
    Main function that initializes and runs the HL7 message processing system.
    """
    # Start Prometheus metrics server
    start_http_server(8000)  # Exposes metrics at http://localhost:8000/metrics
    system_uptime.set(time.time())  # Set system start time

    # Read environment variables for MLLP and pager ports
    mllp_address = os.getenv("MLLP_ADDRESS", "message-simulator:8440")
    pager_address = os.getenv("PAGER_ADDRESS", "message-simulator:8441")

    # ---------------------------------------------------- #
    # Initialization stage
    # ---------------------------------------------------- #
    parser = HL7Parser()
    database = PandasDatabase('data/history.csv')
    pager = Pager(pager_address)
    model = Model()
    data_operator = DataOperator(database, model, pager)
    mllp_listener = MllpListener(mllp_address, parser, data_operator)

    # ---------------------------------------------------- #
    # Running the system
    # ---------------------------------------------------- #
    try:
        while True:
            hl7_messages_received.inc()
            message = mllp_listener.run()

            if message:
                status = data_operator.process_message(message)

                if status:
                    predictions_made.inc()  # Track predictions made

                if pager.last_page_status() == "success":
                    aki_pages_sent.inc()
                elif pager.last_page_status() == "failed":
                    aki_pages_failed.inc()

    except Exception as e:
        print(f"Exception occurred:\n{e}")
        print("Process interrupted")

    # ---------------------------------------------------- #
    # Shutdown stage
    # ---------------------------------------------------- #
    mllp_listener.shutdown()


if __name__ == "__main__":
    main()
