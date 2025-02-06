import os
#import requests
import logging
import socket
import time
from model import Model
from parser import HL7Parser, START_BLOCK, END_BLOCK

import os

# Set the correct host for the HL7 Simulator
# Set the correct host for the HL7 Simulator
SIMULATOR_HOST = os.getenv("SIMULATOR_HOST", "message-simulator")  # Use actual container name
SIMULATOR_PORT = int(os.getenv("SIMULATOR_PORT", "8440"))  # Ensure it's an int

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
#TODO: Add docstrings to the Controller class
#TODO: Make sure failures are handled properly, especially don't re-add measurements if the model fails
class MllpListener:

    def __init__(self, mllp_port, msg_queue):
        self.parser = HL7Parser() #dunno if this is actually needed
        self.mllp_port = mllp_port
        self.msg_queue = msg_queue
        self.client_socket = None
    
    def close_connection(self):
        self.client_socket.close()
        logging.info("[*] Connection closed. Quitting...")
        # i feel like we should exit the system here at this point, see about it later tbh
        exit()
        return


    def hl7_listen(self):
            """Listen for HL7 messages, process them, and assign workers."""
            logging.info(f"[*] Connecting to HL7 Simulator at {SIMULATOR_HOST}:{SIMULATOR_PORT}...")

            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(10)
                client_socket.connect((SIMULATOR_HOST, SIMULATOR_PORT))
                self.client_socket = client_socket
                logging.info("[+] Connected to HL7 Simulator!")

                buffer = b""

                try:
                    data = client_socket.recv(1024)
                    if not data:
                        logging.info("[-] No more data, closing connection.")
                        self.close_connection()

                    buffer += data

                    while START_BLOCK in buffer and END_BLOCK in buffer:
                        start_index = buffer.index(START_BLOCK) + 1
                        end_index = buffer.index(END_BLOCK)
                        hl7_message = buffer[start_index:end_index].decode("utf-8").strip()
                        buffer = buffer[end_index + len(END_BLOCK) :]

                        parsed_message = self.parser.parse(hl7_message)
                        
                        
                        if parsed_message is None or parsed_message[0] is None:
                            logging.error("Received invalid HL7 message or unknown message type.")
                            break  # Prevents further errors
                        #elif parsed_message[0] == "ORU^R01":
                        #    self.process_oru_message(parsed_message)
                        #elif parsed_message[0] == "ADT^A01":
                        #    self.process_adt_message(parsed_message)

                        # TODO: Write to msg_queue
                        self.msg_queue.append(parsed_message)


                        ack_message = self.parser.generate_hl7_ack(hl7_message)
                        client_socket.sendall(ack_message)
                        logging.info(f"[ACK SENT]")

                except socket.timeout:
                    logging.warning("[-] Read timeout. Closing connection.")

                #added this to another function as well, dunno bruh
                client_socket.close()
                logging.info("[*] Connection closed. Quitting...")
                return
                

            except (ConnectionRefusedError, ConnectionResetError):
                logging.error(f"[-] Could not connect to {SIMULATOR_HOST}:{SIMULATOR_PORT}, retrying in 5s...")
                time.sleep(5)
            