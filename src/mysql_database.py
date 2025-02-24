from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base #Safer, automatic sanitizing
from sqlalchemy.dialects.mysql import insert
from datetime import datetime, timezone
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
    creatinine_date = Column(DateTime, primary_key=True, default=datetime.now())
    creatinine_result = Column(Float, nullable=False)

class MySQLDatabase(Database):
    def __init__(self, host, port, user, password, db):
        database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        
        try:
            self.engine = create_engine(database_uri, echo=True)
            self.Session = sessionmaker(bind=self.engine)
            #logging.disable(logging.WARNING)
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
            #existing_patient = self.session.query(Patient).filter_by(mrn=mrn).first()
            stmt = insert(Patient).values(mrn=mrn, age=age, sex=sex)
            stmt = stmt.on_duplicate_key_update(
                age=stmt.inserted.age, 
                sex=stmt.inserted.sex
            )
            self.session.execute(stmt)
            self.session.commit()

            print(f"Added patient with MRN {mrn}.")
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding patient: {e}")

    def add_measurement(self, mrn: str, creatinine_result: float, creatinine_date=None) -> None:
        try:
            creatinine_date = creatinine_date or datetime.now(timezone.utc)
            stmt = insert(Measurement).values(
                mrn=mrn, creatinine_result=creatinine_result, creatinine_date=creatinine_date
            )
            stmt = stmt.on_duplicate_key_update(creatinine_result=stmt.inserted.creatinine_result)
            
            self.session.execute(stmt)
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
    db = MySQLDatabase("localhost","3306","root","password","hospital_db")
    db.connect()
    #print(db.get_data(100005546))
    #TODO: Unit tests
    db.add_patient('12345', 22, 'M')
    
    db.get_data('12345')
    db.add_patient('12345', 23, 'M')
    db.get_data('12345')

    #Test measurements
    sample_datetime = datetime.now()
    db.add_measurement('12345', 1.1, sample_datetime)
    db.get_data('12345')
    db.add_measurement('12345', 1.2, sample_datetime)
    db.get_data('12345')

