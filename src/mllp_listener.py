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
import logging
import socket
import time
import signal
import sys
from src.parser import HL7Parser, START_BLOCK, END_BLOCK

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    - `msg_queue (list)`: Queue for storing parsed messages.
    - `client_socket (socket)`: Active socket connection to the HL7 simulator.
    """

    STATE_FILE = "/aki-system/state/state_backup.txt"

    def __init__(self, mllp_address, msg_queue):
        """
        Initializes the MLLP listener and connects to the HL7 simulator.
        
        Args:
            mllp_address (str): The IP and port of the HL7 simulator.
            msg_queue (list): The message queue to store parsed HL7 messages.
        """
        self.parser = HL7Parser() 
        self.mllp_address = mllp_address
        self.msg_queue = msg_queue
        self.client_socket = None
        self.running = True  # Control flag for safe shutdown
        self.load_state()  # Load saved state if available
        self.open_connection()

        # Register SIGTERM handler
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def open_connection(self):
        """
        Establishes a connection to the HL7 simulator via MLLP.
        Retries every 5 seconds if the connection fails.
        """
        while self.running:
            try:
                mllp_host, mllp_port = self.mllp_address.split(":")
                mllp_port = int(mllp_port)
                logging.info(f"[*] Connecting to HL7 Simulator at {mllp_host}:{mllp_port}...")
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(10)
                client_socket.connect((mllp_host, mllp_port))
                self.client_socket = client_socket
                logging.info("[+] Connected to HL7 Simulator!")
                break
            except (ConnectionRefusedError, ConnectionResetError):
                logging.error(f"[-] Could not connect to {mllp_host}:{mllp_port}, retrying in 5s...")
                time.sleep(5)

    def handle_sigterm(self, signal_num, frame):
        """
        Handles SIGTERM signal for graceful shutdown.
        """
        logging.info(f"[SIGTERM] Received termination signal ({signal_num}). Stopping gracefully...")
        self.running = False  # Stop listener loop
        self.save_state()
        self.shutdown()

    def save_state(self):
        """
        Saves the current state (e.g., messages in queue) before shutdown.
        Ensures that the state file exists before writing.
        """
        try:
            os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
            with open(self.STATE_FILE, "w") as f:
                f.write("\n".join(map(str, self.msg_queue)))  # Convert all messages to strings before saving
            logging.info(f"[STATE] Successfully saved {len(self.msg_queue)} pending messages.")
        except Exception as e:
            logging.error(f"[ERROR] Failed to save state: {e}")

    def load_state(self):
        """
        Loads the saved state from the previous session, if it exists.
        """
        if not os.path.exists(self.STATE_FILE):
            logging.info("[STATE] No previous state found. Starting fresh.")
            return

        try:
            with open(self.STATE_FILE, "r") as f:
                messages = f.read().splitlines()
                if messages:
                    self.msg_queue.extend(messages)
                    logging.info(f"[STATE] Successfully loaded {len(messages)} pending messages. Resending now...")
        except Exception as e:
            logging.error(f"[ERROR] Failed to load saved state: {e}")

    def process_saved_messages(self):
        """
        Processes messages that were loaded from the state file upon restart.
        """
        if not self.msg_queue:
            return  # No saved messages to process

        logging.info(f"[STATE] Reprocessing {len(self.msg_queue)} saved messages...")
        
        for msg in self.msg_queue:
            parsed_message = self.parser.parse(msg)
            if parsed_message is not None and parsed_message[0] is not None:
                ack_message = self.parser.generate_hl7_ack(msg)
                try:
                    self.client_socket.sendall(ack_message.encode("utf-8"))
                    logging.info(f"[ACK SENT] for restored message.")
                except Exception as e:
                    logging.error(f"[ERROR] Failed to resend ACK: {e}")
        
        self.msg_queue.clear()  # Clear queue after reprocessing messages

    def shutdown(self):
        """
        Closes the MLLP connection and safely exits the system.
        """
        if self.client_socket:
            self.client_socket.close()
        logging.info("[*] Connection closed. Quitting...")
        sys.exit(0)

    def hl7_listen(self):
        """
        Listens for HL7 messages, processes them, and stores valid messages in the message queue.
        Receives data over the MLLP connection, extracts messages, and sends an acknowledgment (ACK).
        """
        buffer = b""
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    logging.info("[-] No more data, closing connection.")
                    self.shutdown()
                    break

                buffer += data

                while START_BLOCK in buffer and END_BLOCK in buffer:
                    start_index = buffer.index(START_BLOCK) + 1
                    end_index = buffer.index(END_BLOCK)
                    hl7_message = buffer[start_index:end_index].decode("utf-8").strip()
                    buffer = buffer[end_index + len(END_BLOCK):]

                    parsed_message = self.parser.parse(hl7_message)

                    if parsed_message is None or parsed_message[0] is None:
                        logging.error("Received invalid HL7 message or unknown message type.")
                        break  # Prevents further errors

                    self.msg_queue.append(hl7_message)

                    ack_message = self.parser.generate_hl7_ack(hl7_message)
                    self.client_socket.sendall(ack_message.encode("utf-8"))
                    logging.info(f"[ACK SENT]")

            except socket.timeout:
                logging.warning("[-] Read timeout. Closing connection.")

    def run(self):
        """
        Starts the HL7 listener and processes saved messages on startup.
        """
        self.process_saved_messages()  # Reprocess messages before listening for new ones
        while self.running:
            self.hl7_listen()
