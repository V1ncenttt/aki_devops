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
from src.parser import HL7Parser, START_BLOCK, END_BLOCK
from src.data_operator import DataOperator

import os

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

    def __init__(self, mllp_address: str, parser: HL7Parser, data_operator: DataOperator):
        """
        Initializes the MLLP listener and connects to the HL7 simulator.
        
        Args:
            mllp_address (str): The IP and port of the HL7 simulator.
            msg_queue (list): The message queue to store parsed HL7 messages.
        """
        self.parser = parser 
        self.mllp_address = mllp_address
        self.data_operator = data_operator
        self.client_socket = None
        self.open_connection()
    
    def open_connection(self):
        """
        Establishes a connection to the HL7 simulator via MLLP.
        Retries every 5 seconds if the connection fails.
        """
        while True:
            try:
                mllp_host = self.mllp_address.split(":")[0]
                mllp_port = int(self.mllp_address.split(":")[1])
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
        return



    def shutdown(self):
        """
        Closes the connection and exits the system.
        """
        self.client_socket.close()
        logging.info("[*] Connection closed. Quitting...")
        exit()
        return
    
    def send_ack(self, hl7_message):
        # Invariant: Patient from 'parsed_message' has been processed correctly
        # now at the very end we send an ack, maybe move this to main.py
        ack_message = self.parser.generate_hl7_ack(hl7_message)
        self.client_socket.sendall(ack_message)
        logging.info(f"[ACK SENT]")
        return


    def run(self):
        """
        Listens for HL7 messages, processes them, and stores valid messages in the message queue.
        
        Receives data over the MLLP connection, extracts messages, and sends an acknowledgment (ACK).
        """

        buffer = b""
        while True: # should we replace this while true with smth
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    logging.info("[-] No more data, closing connection.")
                    self.shutdown()

                buffer += data

                while START_BLOCK in buffer and END_BLOCK in buffer:
                    start_index = buffer.index(START_BLOCK) + 1
                    end_index = buffer.index(END_BLOCK)
                    hl7_message = buffer[start_index:end_index].decode("utf-8").strip()
                    buffer = buffer[end_index + len(END_BLOCK) :]

                    parsed_message = self.parser.parse(hl7_message)
                    
                    
                    if parsed_message is None or parsed_message[0] is None:
                        logging.error("Received invalid HL7 message or unknown message type:")
                        logging.error(f"{parsed_message}")
                        # return back to main.py without sending an ACK
                        # TODO: introduce some safety mechanism here
                        return

                    # Invariant: message is parsed correctly
                    try:
                        # forward message to data_operator for further processing
                        status = self.data_operator.process_message(parsed_message)

                        # return the parsed_message to main.py so that it knows everything worked 
                        # and can then send the ack-message
                        if status:
                            self.send_ack(hl7_message)
                        else:
                            # TODO: Implement safety mechanism if status is false!
                            logging.error(f"Some error occured, check logs. Did not process the following message correctly:\n{hl7_message}")
                        return

                    except Exception as e:
                        # log the error
                        logging.error(f"Data Operator could not process message! \nError received: \n\n{e}")
                        # and return to main.py system loop without sending an ACK message
                        # TODO: implement/check fail safety mechanisms
                        return

                    

            except socket.timeout:
                logging.warning("[-] Read timeout. Closing connection.")
                