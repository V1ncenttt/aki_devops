"""
MLLP Listener Module
====================
This module provides the `MllpListener` class, which listens for HL7 messages over an MLLP connection, 
processes them, and assigns tasks accordingly.

Authors:
--------
- Vincent Lefeuve (vincent.lefeuve24@imperial.ac.uk)

Classes:
--------
- `MllpListener`: Listens for HL7 messages, processes them, and assigns tasks.

Usage:
------
Example:
    listener = MllpListener("127.0.0.1:5000", msg_queue)
    listener.run()

"""

import os
import csv
import logging
import socket
import time
import signal
from src.parser import HL7Parser, START_BLOCK, END_BLOCK
from src.data_operator import DataOperator
from src.metrics import HL7_MESSAGES_RECEIVED, INCORRECT_MESSAGES_RECEIVED, MLLP_RECONNECTIONS, MLLP_SHUTDOWNS, FAILED_MESSAGES, PARSED_MESSAGES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
failed_file_path = "/aki-system/state/failed_messages.csv"
parsed_file_path = "/aki-system/state/parsed_messages.csv"


class MllpListener:
    """
    MLLP Listener for HL7 Messages
    ===============================
    This class listens for HL7 messages over an MLLP connection, processes them, 
    and assigns workers to handle the received messages.

    Attributes:
    -----------
    - `parser (HL7Parser)`: HL7 message parser.
    - `mllp_address (str)`: The address (host:port) of the HL7 simulator.
    - `data_operator (DataOperator)`: Handles processing of parsed messages.
    - `client_socket (socket)`: Active socket connection to the HL7 simulator.
    """

    def __init__(self, mllp_address: str, parser: HL7Parser, data_operator: DataOperator):
        """
        Initializes the MLLP listener and connects to the HL7 simulator.
        
        Args:
            mllp_address (str): The IP and port of the HL7 simulator.
            parser (HL7Parser): Parser for HL7 messages.
            data_operator (DataOperator): Component handling parsed message processing.
        """
        self.parser = parser 
        self.mllp_address = mllp_address
        self.data_operator = data_operator
        self.client_socket = None
        self.running = True  # Track listener state
        
        # Ensure storage directory and files exist
        # This will create the file if it doesn't exist
        self.ensure_file_exists(failed_file_path, ["Message"])
        self.ensure_file_exists(parsed_file_path, ["Message"])
        
        self.open_connection()
    
    def ensure_file_exists(self, file_path, headers):
        """ Creates a CSV file with headers if it doesn't exist. """
        # Ensure directory exists
        # Ensure directory exists (important!)
        os.makedirs('/aki-system/state', exist_ok=True)

        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)  # Write headers only if file is newly created

    def open_connection(self):
        """
        Establishes a connection to the HL7 simulator via MLLP.
        Retries every 5 seconds if the connection fails.
        """
        while self.running:
            MLLP_RECONNECTIONS.inc()
            try:
                mllp_host, mllp_port = self.mllp_address.split(":")
                mllp_port = int(mllp_port)
                
                logging.info(f"mllp_listener.py: [*] Connecting to HL7 Simulator at {mllp_host}:{mllp_port}...")
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(None)
                self.client_socket.connect((mllp_host, mllp_port))
                
                logging.info("mllp_listener.py: [+] Connected to HL7 Simulator!")
                return
            except (ConnectionRefusedError, ConnectionResetError):
                logging.error(f"mllp_listener.py: [-] Could not connect to {mllp_host}:{mllp_port}, retrying in 5s...")
                time.sleep(5)

    def shutdown(self):
        """
        Gracefully shuts down the MLLP listener.
        Closes the connection and increments the shutdown counter.
        """
        if self.client_socket:
            self.client_socket.close()
        
        MLLP_SHUTDOWNS.inc()  # Track shutdowns
        logging.info(f"mllp_listener.py: [*] Shutting down MLLP Listener. Total shutdowns: {MLLP_SHUTDOWNS._value.get()}")
        self.running = False
        exit()

    def send_ack(self, hl7_message):
        """
        Sends an acknowledgment (ACK) message for a successfully processed HL7 message.

        Args:
            hl7_message (str): The received HL7 message to acknowledge.
        """
        try:
            ack_message = self.parser.generate_hl7_ack(hl7_message)
            self.client_socket.sendall(ack_message)
        except Exception as e:
            logging.error(f"mllp_listener.py: Failed to send ACK: {e}")
        logging.info("mllp_listener.py: [ACK SENT]")
        return
    
    
    def record_messages(self):
        """ 
        Writes failed and parsed messages to respective CSV files.
        """
        try:
            if FAILED_MESSAGES:
                with open(failed_file_path, 'a', newline='') as failed_file:
                    failed_writer = csv.writer(failed_file)
                    for msg in FAILED_MESSAGES:
                        failed_writer.writerow([msg])
                FAILED_MESSAGES.clear()  # Prevent duplicate writes
        except Exception as e:
            logging.error(f"mllp_listener.py: Error writing to failed messages file: {e}")

        try:
            if PARSED_MESSAGES:
                with open(parsed_file_path, 'a', newline='') as parsed_file:
                    parsed_writer = csv.writer(parsed_file)
                    for msg in PARSED_MESSAGES:
                        parsed_writer.writerow([msg])
                PARSED_MESSAGES.clear()  # Prevent duplicate writes
        except Exception as e:
            logging.error(f"mllp_listener.py: Error writing to parsed messages file: {e}")

    
    def run(self):
        """
        Listens for HL7 messages, processes them, and sends an acknowledgment (ACK).
        """

        buffer = b""
        try:
            while self.running:
                try:
                    data = self.client_socket.recv(1024)
                    if not data:
                        logging.info("mllp_listener.py: [-] No more data, closing connection.")
                        self.shutdown()
                        return

                    buffer += data

                    while START_BLOCK in buffer and END_BLOCK in buffer:
                        start_index = buffer.index(START_BLOCK) + 1
                        end_index = buffer.index(END_BLOCK)
                        hl7_message = buffer[start_index:end_index].decode("utf-8").strip()
                        buffer = buffer[end_index + len(END_BLOCK):]

                        parsed_message = self.parser.parse(hl7_message)

                        if parsed_message is None or parsed_message[0] is None:
                            logging.error("mllp_listener.py: Received invalid HL7 message or unknown message type.")
                            INCORRECT_MESSAGES_RECEIVED.inc()
                            return

                        HL7_MESSAGES_RECEIVED.inc()
                        PARSED_MESSAGES.append(hl7_message)
                        FAILED_MESSAGES.append('alisoncheck')

                        try:
                            logging.info("mllp_listener.py: Forwarding hl7 message to data operator")
                            status = self.data_operator.process_message(parsed_message)

                            if status:
                                self.send_ack(hl7_message)
                            else:
                                logging.error(f"mllp_listener.py: Error processing message:\n{hl7_message}")
                                FAILED_MESSAGES.append(hl7_message)
                            
                            
                            
                            # CHECK the file path for kubernetes 
                            # This calls function to record all messages
                            self.record_messages()

                        except Exception as e:
                            logging.error(f"mllp_listener.py: Error {e}")

                        return

                except socket.timeout:
                    logging.warning("mllp_listener.py: [-] Read timeout. Closing connection.")
                    self.shutdown()
                    return

        except KeyboardInterrupt:
            logging.info("mllp_listener.py: [*] Keyboard interrupt detected. Shutting down gracefully...")
            self.shutdown()

# Handle termination signals for graceful shutdown
def handle_shutdown_signal(signum, frame):
    logging.info(f"mllp_listener.py: [*] Received shutdown signal ({signum}). Shutting down...")
    listener.shutdown()

signal.signal(signal.SIGINT, handle_shutdown_signal)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, handle_shutdown_signal)  # Handle termination signals
                