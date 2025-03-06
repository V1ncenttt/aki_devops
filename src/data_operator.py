import logging
"""
Data Operator Module
====================
This module provides the `DataOperator` class, which processes HL7 messages, manages patient records, 
and queues predictions for AKI detection.

Authors:
--------
- Kerim Birgi (kerim.birgi24@imperial.ac.uk)
- Alison Lupton (alison.lupton24@imperial.ac.uk)

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
from src.database import Database
from src.model import Model
from src.pager import Pager
from src.metrics import BLOOD_TEST_RESULTS_RECEIVED, PREDICTIONS_MADE, POSITIVE_PREDICTIONS_MADE, PREDICTIONS_FAILED, ADMITTED_PATIENT_MESSAGES, DISCHARGED_PATIENT_MESSAGES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DataOperator:
    """
    Data Operator for HL7 Message Processing
    ========================================
    Handles incoming HL7 messages, updates patient records, and prepares data for prediction.
    """
    def __init__(self, database: Database, model: Model, pager: Pager):
        """
        Initializes the DataOperator with the database, model, and pager.

        Args:
            database (Database): Patient record management.
            model (Model): AKI prediction model.
            pager (Pager): Pager system for alerts.
        """
        self.database = database
        self.model = model
        self.pager = pager

    def process_patient(self, mrn, creatinine_value, test_time) -> int:
        """
        Processes patient data by retrieving past measurements and making AKI predictions.

        Args:
            mrn (int): Patient's medical record number.
            creatinine_value (float): Latest creatinine test result.
            test_time (str): Timestamp of the test.

        Returns:
            int: Status code for the processing operation. 0 for success, 1 for database error, 2 for model error.
        """
        logging.info(f"data_operator.py: [WORKER] Processing Patient {mrn} at {test_time}...")
        
        # Measurment added first 
        status = self.database.add_measurement(mrn, creatinine_value, test_time) 
        
        if not status:
            logging.error(f"data_operator.py: Error adding measurement for patient {mrn}, database might be disconnected")
            return 1
        
        status, patient_vector = self.database.get_data(mrn) # Pull all data, including new measurment
        
        if not status:
            logging.error(f"data_operator.py: Error getting data for patient {mrn}, database might be disconnected")
            return 1

                
        # Convert `measurement_date` to UNIX timestamp for XGBoost compatibility
        if "measurement_date" in patient_vector.columns:
            patient_vector["measurement_date"] = patient_vector["measurement_date"].astype("int64") // 10**9

        
        # if aki-prediction is positive, send a pager alert
        try:
            positive_prediction = self.model.predict_aki(patient_vector)
            PREDICTIONS_MADE.inc()
        except Exception as e:
            logging.error(f"data_operator.py: Error from model.py\nException:\n{e}")
            PREDICTIONS_FAILED.inc()  # Track failed predictions
            return 2 #Might need to have more statuses here, eg 0 for OK, 1 for db disconnected, 2 for model error, ...
        
        if positive_prediction:
            POSITIVE_PREDICTIONS_MADE.inc()
            self.pager.send_pager_alert(mrn, test_time)

        return 0

    def process_adt_message(self, message) -> int:  
        """
        Processes an ADT (Admission, Discharge, Transfer) HL7 message 
        to update the patient database.

        Args:
            message (tuple): Parsed HL7 message containing patient data.

        Returns:
            bool: True if processing was successful.
        """
        mrn = message[1]["mrn"]
        name = message[1]["name"]
        age = message[1]["age"]
        sex = message[1]['sex']


        status = self.database.add_patient(mrn, age, sex) #Might add more status types eg 0 for OK, 1 for db disconnected, ...
        if not status:
            logging.error(f"data_operator.py: Error adding patient {name} with MRN {mrn} to the database")
            return 1
        
        logging.info(f"data_operator.py: Patient {name} with MRN {mrn} added to the database")

        return 0

    def process_oru_message(self, message):
        """
        Processes an ORU (Observation Result) HL7 message, 
        extracting test results and processing patient data.

        Args:
            message (tuple): Parsed HL7 message containing test results.

        Returns:
            bool: True if a prediction was made, False otherwise.
        """
        mrn = message[2][0]["mrn"]
        creatinine_value = message[2][0]["test_value"]
        test_time = message[2][0]["test_time"]

        logging.info(f"data_operator.py: Patient {mrn} has creatinine value {creatinine_value} at {test_time}")
        status = self.process_patient(mrn, creatinine_value, test_time)
        return status

    def process_message(self, message) -> int:
        """
        Determines the type of HL7 message and processes it accordingly.

        Args:
            message (tuple): Parsed HL7 message.

        Returns:
            int: Status code for the processing operation. 0 for success, 1 for database error, 2 for model error, 3 for unknown message type.
        """

        if message[0] == "ORU^R01":
            BLOOD_TEST_RESULTS_RECEIVED.inc()
            logging.info("data_operator.py: Logging ORU^R01 Message")
            status = self.process_oru_message(message) 
        elif message[0] == "ADT^A01":
            ADMITTED_PATIENT_MESSAGES.inc()
            logging.info("data_operator.py: Logging ADT^A01 Message")
            status = self.process_adt_message(message) 
        elif message[0] == "ADT^A03":
            DISCHARGED_PATIENT_MESSAGES.inc()
            status = 0
        else:
            logging.error(f"data_operator.py: Unknown Message type {message}")
            status = 3
        
        return status  # Ensures `main.py` knows if prediction was successful and the type of error if not
