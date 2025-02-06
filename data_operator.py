import logging
from pandas_database import PandasDatabase
import json 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DataOperator:
    def __init__(self):
        self.database = PandasDatabase('history.csv') #TODO: Change it later to be out of this and set in main
        with open('expected_columns.json', 'r') as f: # there should be a better way to do this check i think, maybe not even necessary, see later
            self.expected_columns = json.load(f) # TODO: understand this!

    def add_patient(self, mrn, age=None, sex=None):
        """_summary_

        Args:
            mrn (_type_): _description_
            age (_type_, optional): _description_. Defaults to None.
        """
        return self.database.add_patient(mrn, age,sex)

    def process_patient(self, mrn, creatinine_value, test_time):
        logging.info(f"[WORKER] Processing Patient {mrn} at {test_time}...")

        patient_vector = self.model.get_past_measurements(mrn, creatinine_value, test_time)

        alert_needed = self.model.predict_aki(patient_vector)
        logging.info(f"prediction_made:{alert_needed}")

        if alert_needed:
            self.send_pager_alert(mrn, test_time)

        self.model.add_measurement(mrn, creatinine_value, test_time)

    def process_adt_message(self, message):  
        mrn = message[1]["mrn"]
        name = message[1]["name"]
        age = message[1]["age"]
        sex = message[1]['gender']

        self.add_patient(mrn, age, sex)

        logging.info(f"Patient {name} with MRN {mrn} added to the database")

    def process_oru_message(self, message):
        mrn = message[2][0]["mrn"]
        creatinine_value = message[2][0]["test_value"]
        test_time = message[2][0]["test_time"]


        logging.info(f"Patient {mrn} has creatinine value {creatinine_value} at {test_time}")
        self.process_patient(mrn, creatinine_value, test_time)

    def process_message(self, message):
        if message[0] == "ORU^R01":
            self.process_oru_message(message)
        elif message[0] == "ADT^A01":
            self.process_adt_message(message)