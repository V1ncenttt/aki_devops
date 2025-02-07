"""
Data Operator Module
====================
This module provides the `DataOperator` class, which processes HL7 messages, manages patient records, 
and queues predictions for AKI detection.

Authors:
--------
- Kerim Birgi (kerim.birgi24@imperial.ac.uk)
- Alsion Lupton (alison.lupton24@imperial.ac.uk)

Classes:
--------
- `DataOperator`: Handles patient data storage, processing, and prediction queuing.

Usage:
------
Example:
    database = Database()
    operator = DataOperator(msg_queue, predict_queue, database)
    operator.run()

"""

import logging
from database import Database
import json 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DataOperator:
    """
    Data Operator for HL7 Message Processing
    ========================================
    Handles incoming HL7 messages, updates patient records, and prepares data for prediction.
    
    Attributes:
    -----------
    - `database (Database)`: Instance of the patient database.
    - `expected_columns (dict)`: Expected column names for data consistency.
    - `msg_queue (list)`: Queue for storing incoming HL7 messages.
    - `predict_queue (list)`: Queue for storing patient data for prediction.
    """
    def __init__(self, msg_queue, predict_queue, database: Database):
        """
        Initializes the DataOperator with message and prediction queues, and a patient database.
        
        Args:
            msg_queue (list): Queue for storing incoming HL7 messages.
            predict_queue (list): Queue for storing patient data for prediction.
            database (Database): Database instance for patient record management.
        """
        self.database = database 
        self.msg_queue = msg_queue
        self.predict_queue = predict_queue


    def process_patient(self, mrn, creatinine_value, test_time):
        """
        Processes patient data by retrieving past measurements and queueing for prediction.
        
        Args:
            mrn (int): Patient's medical record number.
            creatinine_value (float): Latest creatinine test result.
            test_time (str): Timestamp of the test.
        """
        logging.info(f"[WORKER] Processing Patient {mrn} at {test_time}...")

        patient_vector = self.database.get_past_measurements(mrn, creatinine_value, test_time)
        
        self.predict_queue.append((mrn, test_time, patient_vector))

        self.database.add_measurement(mrn, creatinine_value, test_time)     


    def process_adt_message(self, message):  
        """
        Processes an ADT (Admission, Discharge, Transfer) HL7 message 
        to update the patient database.
        
        Args:
            message (tuple): Parsed HL7 message containing patient data.
        
        Returns:
            bool: False to indicate processing was successful but no prediction was made.
        """
        mrn = message[1]["mrn"]
        name = message[1]["name"]
        age = message[1]["age"]
        sex = message[1]['gender']

        self.database.add_patient(mrn, age, sex)

        logging.info(f"Patient {name} with MRN {mrn} added to the database")
        return False
        

    def process_oru_message(self, message):
        """
        Processes an ORU (Observation Result) HL7 message,
        extracting test results and processing patient data.
        
        Args:
            message (tuple): Parsed HL7 message containing test results.
        
        Returns:
            bool: True to indicate prediction processing was initiated.
        """
        mrn = message[2][0]["mrn"]
        creatinine_value = message[2][0]["test_value"]
        test_time = message[2][0]["test_time"]

        logging.info(f"Patient {mrn} has creatinine value {creatinine_value} at {test_time}")
        self.process_patient(mrn, creatinine_value, test_time)
        return True

    def process_message(self, message):
        """
        Determines the type of HL7 message and processes it accordingly.
        
        Args:
            message (tuple): Parsed HL7 message.
        
        Returns:
            bool: True if a prediction was made, False otherwise.
        """
        if message[0] == "ORU^R01":
            return self.process_oru_message(message) # need to return false after 
        elif message[0] == "ADT^A01":
            return self.process_adt_message(message) # need to return true after 
            
    def run(self):
        """
        Executes the processing of the next message in the queue.
        """
       
        # input is parsed message 
        message = self.msg_queue.pop(0)
        
        if message is None or message[0] is None:
            logging.error("Received invalid HL7 message or unknown message type.")
            return  # Stop errors
        else:
            return self.process_message(message)
