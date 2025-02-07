import os
#import requests
import logging
import socket
import time
from model import Model
from parser import HL7Parser, START_BLOCK, END_BLOCK

import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
#TODO: Add docstrings to the Controller class
#TODO: Make sure failures are handled properly, especially don't re-add measurements if the model fails
class MllpListener:

    def __init__(self, mllp_address, msg_queue):
        self.parser = HL7Parser() #dunno if this is actually needed
        self.mllp_address = mllp_address
        self.msg_queue = msg_queue
        self.client_socket = None
        self.open_connection()
    
    def open_connection(self):
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
        for closing the connection
        """
        self.client_socket.close()
        logging.info("[*] Connection closed. Quitting...")
        # i feel like we should exit the system here at this point, see about it later tbh
        exit()
        return


    def hl7_listen(self):
            """Listen for HL7 messages, process them, and assign workers."""

                #client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #client_socket.settimeout(10)
                #client_socket.connect((SIMULATOR_HOST, SIMULATOR_PORT))
                #self.client_socket = client_socket
                #logging.info("[+] Connected to HL7 Simulator!")

            buffer = b""
            while True:
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

                        #currently everything is being parsed here, we can modularize this if we wish to make it even more modular
                        parsed_message = self.parser.parse(hl7_message)
                        
                        
                        if parsed_message is None or parsed_message[0] is None:
                            logging.error("Received invalid HL7 message or unknown message type.")
                            break  # Prevents further errors

                        # TODO: Write to msg_queue
                        self.msg_queue.append(parsed_message)


                        ack_message = self.parser.generate_hl7_ack(hl7_message)
                        self.client_socket.sendall(ack_message)
                        logging.info(f"[ACK SENT]")
                        return

                except socket.timeout:
                    logging.warning("[-] Read timeout. Closing connection.")

                #added this to another function as well, dunno bruh
                #self.client_socket.close()
                #logging.info("[*] Connection closed. Quitting...")
                #return
    
    def run(self):
        self.hl7_listen()
        return
            