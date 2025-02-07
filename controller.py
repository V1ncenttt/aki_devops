"""
HL7 Controller Module
=====================
This module provides the `Controller` class, which listens for HL7 messages, 
processes patient data, and triggers alerts based on model predictions.

Authors:
--------
- Kerim Birgi (kerim.birgi24@imperial.ac.uk)

Classes:
--------
- `Controller`: Listens for HL7 messages, processes patient data, and triggers alerts.

Usage:
------
Example:
    model = Model("history.csv")
    controller = Controller(model, "127.0.0.1:5000")
    controller.hl7_listen("127.0.0.1:6000")

"""

import os
import requests
import logging
import socket
import time
from model import Model
from parser import HL7Parser, START_BLOCK, END_BLOCK
import os


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Controller:
    """
    HL7 Listener & Worker Controller
    =================================
    Listens for HL7 messages, processes patient data, and triggers alerts if necessary.
    
    Attributes:
    -----------
    - `model (Model)`: The model instance for AKI detection.
    - `pager_url (str)`: The URL of the pager system.
    - `parser (HL7Parser)`: HL7 message parser.
    - `counter (int)`: Counts the number of processed patients.
    """

    def __init__(self, model, pager_address):
        """
        Initializes the Controller with a model and pager address.
        
        Args:
            model (Model): The predictive model for AKI detection.
            pager_address (str): The IP and port of the pager system.
        """
        self.model = model
        pager_host = pager_address.split(":")[0]
        pager_port = pager_address.split(":")[1]
        self.pager_url = f"http://{pager_host}:{pager_port}/page"        
        self.parser = HL7Parser()
        self.counter = 0
       
    def process_patient(self, mrn, creatinine_value, test_time):
        """
        Processes patient data by retrieving past measurements, making a prediction, 
        and triggering a pager alert if necessary.
        
        Args:
            mrn (int): Patient's medical record number.
            creatinine_value (float): The latest creatinine test result.
            test_time (str): The timestamp of the test.
        """
        patient_vector = self.model.get_past_measurements(mrn, creatinine_value, test_time)
        alert_needed = self.model.predict_aki(patient_vector)
        logging.info(f"prediction_made:{alert_needed}")
        self.counter += 1
        logging.info(f"\033[1;32m>>> HELLO!!!!!! Processing Patient {self.counter} <<<\033[0m")

        if alert_needed:
            self.send_pager_alert(mrn, test_time)

        self.model.add_measurement(mrn, creatinine_value, test_time)


    def process_adt_message(self, message):  
        """
        Processes an ADT (Admission, Discharge, Transfer) HL7 message 
        to update the patient database.
        
        Args:
            message (tuple): Parsed HL7 message containing patient data.
        """
        mrn = message[1]["mrn"]
        name = message[1]["name"]
        age = message[1]["age"]
        sex = message[1]['gender']

        self.model.add_patient(mrn, age, sex)


    def process_oru_message(self, message):
        """
        Processes an ORU (Observation Result) HL7 message, 
        extracting test results and processing patient data.
        
        Args:
            message (tuple): Parsed HL7 message containing test results.
        """
        mrn = message[2][0]["mrn"]
        creatinine_value = message[2][0]["test_value"]
        test_time = message[2][0]["test_time"]

        self.process_patient(mrn, creatinine_value, test_time)

        

    def hl7_listen(self, mllp_address):
        """
        Listens for HL7 messages, processes them, and assigns workers accordingly.
        
        Args:
            mllp_address (str): The IP and port of the HL7 simulator.
        """
        mllp_host = mllp_address.split(":")[0]
        mllp_port = int(mllp_address.split(":")[1])
        logging.info(f"[*] Connecting to HL7 Simulator at {mllp_host}:{mllp_port}...")

        while True:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(10)
                client_socket.connect((mllp_host, mllp_port))
                logging.info("[+] Connected to HL7 Simulator!")

                buffer = b""

                while True:
                    try:
                        data = client_socket.recv(1024)
                        if not data:
                            logging.info("[-] No more data, closing connection.")
                            break

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
                            elif parsed_message[0] == "ORU^R01":
                                self.process_oru_message(parsed_message)
                            elif parsed_message[0] == "ADT^A01":
                                self.process_adt_message(parsed_message)

                            ack_message = self.parser.generate_hl7_ack(hl7_message)
                            client_socket.sendall(ack_message)

                    except socket.timeout:
                        logging.warning("[-] Read timeout. Closing connection.")
                        break

                client_socket.close()
                logging.info("[*] Connection closed. Quitting...")
                return
                

            except (ConnectionRefusedError, ConnectionResetError):
                logging.error(f"[-] Could not connect to {mllp_host}:{mllp_port}, retrying in 5s...")
                time.sleep(5)

    def send_pager_alert(self, mrn, timestamp):
        """
        Sends a pager alert asynchronously.
        """
        timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "").replace('T', '').split('.')[0]

        logging.info(f"[*] Sending pager alert for Patient {mrn} at {timestamp}...")

        content = f"{mrn},{timestamp}"

        for _ in range(3):  # Retry 3 times if there is a failure
            try:
                response = requests.post(self.pager_url, data=content, timeout=5)
                response.raise_for_status()
                return
            except requests.RequestException as e:
                logging.warning(f"[ALERT FAILED] Retrying... {e}")
                time.sleep(1)  # Wait before retrying


def main():
    model = Model("history.csv")
    controller = Controller(model)
    controller.hl7_listen()

    

if __name__ == "__main__":
    main()
