from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base #Safer, automatic sanitizing
from datetime import datetime
from src.database import Database
import pandas as pd
import logging

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'Patients'
    mrn = Column(String(50), primary_key=True)
    age = Column(Integer, nullable=True)
    sex = Column(Enum('M', 'F', 'Other'), nullable=True)

class Measurement(Base):
    __tablename__ = 'Measurements'
    mrn = Column(String(50), ForeignKey('Patients.mrn', ondelete="CASCADE"), primary_key=True)
    creatinine_date = Column(DateTime, primary_key=True, default=datetime.utcnow)
    creatinine_result = Column(Float, nullable=False)

class MySQLDatabase(Database):
    def __init__(self, host, port, user, password, db):
        database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        
        try:
            self.engine = create_engine(database_uri, echo=True)
            self.Session = sessionmaker(bind=self.engine)
            print("MySQL database object created.")
        except SQLAlchemyError as e:
            print(f"Error initializing database connection: {e}")
    

    def connect(self):
        self.session = self.Session()
        print("Connected to MySQL database.")

    def disconnect(self):
        self.session.close()
        print("Disconnected from MySQL database.")

    def add_patient(self, mrn: str, age: int = None, sex: str = None) -> None:
        try:
            existing_patient = self.session.query(Patient).filter_by(mrn=mrn).first()
        
            # TODO: Check if this is ok
            if existing_patient:
                #logging.warning(f" DUPLICATE PATIENT FOUND!!!: MRN {mrn}")
                # logging.warning(f" Existing Patient in DB: Age={existing_patient.age}, Sex={existing_patient.sex}")
                # logging.warning(f"Incoming Patient Data: Age={age}, Sex={sex}")
                #logging.warning("This patient will not be added to the database")
                return
                
            patient = Patient(mrn=mrn, age=age, sex=sex)
            self.session.add(patient)
            self.session.commit()
            print(f"Added patient with MRN {mrn}.")
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding patient: {e}")

    def add_measurement(self, mrn: str, creatinine_result: float, creatinine_date=None) -> None:
        try:
            
            existing_measurement = (
            self.session.query(Measurement)
            .filter_by(mrn=mrn, creatinine_date=creatinine_date)
            .first()
            )
            
            if existing_measurement:
                logging.warning(f" DUPLICATE MEASUREMENT FOUND! MRN: {mrn}")
                logging.warning(f"Existing Measurement: Value={existing_measurement.creatinine_result}, Date={existing_measurement.creatinine_date}")
                logging.warning(f"Incoming Measurement: Value={creatinine_result}, Date={creatinine_date}")
                return  # Exit early to prevent duplicate insert
            
            
            
            creatinine_date = creatinine_date or datetime.now(datetime.zone.utc)  
            
            #datetime.utcnow() 
            measurement_entry = Measurement(mrn=mrn, creatinine_result=creatinine_result, creatinine_date=creatinine_date)
            self.session.add(measurement_entry)
            self.session.commit()
            print(f"Added measurement for MRN {mrn}.")
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding measurement: {e}")

    def get_data(self, mrn: str):
        """
        Retrieves historical creatinine measurements for a given patient as a pandas DataFrame.

        Args:
            mrn (str): Medical record number (MRN) of the patient.

        Returns:
            DataFrame: DataFrame with columns ['creatinine_date', 'creatinine_result'] sorted by date.
        """
        
        #NOTE: the return value of this should be a "patient vector" that gets passed to the predict queue with
        # the other metrics as: self.predict_queue.append((mrn, test_time, patient_vector))
        # flow is then to predict_aki --> preprocess --> process_features, so this needs to be the right 
        # format for model.process_features basically
        #NOTE: I am returning this as a df right now bc that's what the model wants, but if you want to change this to be a tuple 
        # that's fine we just have to fix the model 


        try:
            # Query both tables to get measurements and  patient info
            
            patient_data = self.session.query(Patient.age, Patient.sex).filter_by(mrn=mrn).first()
            if not patient_data:
                logging.warning(f"No patient found for MRN {mrn}")
                return pd.DataFrame()  # empty df if patient doesn't exist (I don't think this should happen)
            
            age, sex = patient_data.age, patient_data.sex
            measurements = (
            self.session.query(Measurement.creatinine_date, Measurement.creatinine_result)
            .filter_by(mrn=mrn)
            .order_by(Measurement.creatinine_date.asc())
            .all()
            )

            # Convert results to DataFrame
            # Convert to DataFrame
            df = pd.DataFrame(measurements, columns=['creatinine_date', 'creatinine_result'])

            # Step 3: Ensure datetime format for processing
            df['creatinine_date'] = pd.to_datetime(df['creatinine_date'], errors='coerce')

            # Step 4: Convert to Feature Vector (Flatten)
            flattened_features = {
                'age': age,
                'sex': sex,
            }

            # Convert measurement history to columns like creatinine_date_0, creatinine_result_0, etc.
            for i, row in df.iterrows():
                flattened_features[f'creatinine_date_{i}'] = row['creatinine_date']
                flattened_features[f'creatinine_result_{i}'] = row['creatinine_result']

            # Step 5: Convert to DataFrame (Single Row)
            feature_df = pd.DataFrame([flattened_features])

            return feature_df
            
            

            

        except SQLAlchemyError as e:
            logging.error(f"Error retrieving data for MRN {mrn}: {e}")
            return pd.DataFrame(columns=['creatinine_date', 'creatinine_result', 'age', 'sex'])


        
        
        

if __name__ == "__main__":
    db = MySQLDatabase("localhost","3306","root","passwosrd","hospital_db")
    db.connect()
    print(db.get_data(100005546))
    #TODO: Unit tests

