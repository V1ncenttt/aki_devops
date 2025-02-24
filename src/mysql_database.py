from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base #Safer, automatic sanitizing
from datetime import datetime
from database import Database
import pandas as pd


Base = declarative_base()

class Patient(Base):
    __tablename__ = 'Patients'
    mrn = Column(String(50), primary_key=True)
    age = Column(Integer, nullable=True)
    sex = Column(Enum('M', 'F', 'Other'), nullable=True)

class Measurement(Base):
    __tablename__ = 'Measurements'
    mrn = Column(String(50), ForeignKey('Patients.mrn', ondelete="CASCADE"), primary_key=True)
    measurement_date = Column(DateTime, primary_key=True, default=datetime.utcnow)
    measurement_value = Column(Float, nullable=False)

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
            patient = Patient(mrn=mrn, age=age, sex=sex)
            self.session.add(patient)
            self.session.commit()
            print(f"Patient with MRN {mrn} added/updated.")
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding/updating patient: {e}")

    def add_measurement(self, mrn: str, measurement_value: float, measurement_date=None) -> None:
        try:
            measurement_date = measurement_date or datetime.utcnow() #TODO: I think this is the correct way instead of the below
            # measurement_date = measurement_date or datetime.now(datetime.zone.utc)  
            measurement_entry = Measurement(mrn=mrn, measurement_value=measurement_value, measurement_date=measurement_date)
            self.session.add(measurement_entry)
            self.session.commit()
            print(f"Measurement for MRN {mrn} on {measurement_date} added/updated.")
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding measurement: {e}")

    def get_data(self, mrn: str):
        """
        Retrieves historical creatinine measurements for a given patient as a pandas DataFrame.

        Args:
            mrn (str): Medical record number (MRN) of the patient.

        Returns:
            DataFrame: DataFrame with columns ['measurement_date', 'measurement_value'] sorted by date.
        """
        
        #NOTE: the return value of this should be a "patient vector" that gets passed to the predict queue with
        # the other metrics as: self.predict_queue.append((mrn, test_time, patient_vector))
        # flow is then to predict_aki --> preprocess --> process_features, so this needs to be the right 
        # format for model.process_features basically
        #NOTE: I am returning this as a df right now bc that's what the model wants, but if you want to change this to be a tuple 
        # that's fine we just have to fix the model 


        try:
            data = (
                self.session.query(Measurement.measurement_date, Measurement.measurement_value)
                .filter_by(mrn=mrn)
                .order_by(Measurement.measurement_date.asc())
                .all()
            )
            df = pd.DataFrame(data, columns=['measurement_date', 'measurement_value'])

            # Ensure measurement_date is in datetime format
            df['measurement_date'] = pd.to_datetime(df['measurement_date'], errors='coerce')

            return df

        except SQLAlchemyError as e:
            print(f"Error retrieving data: {e}")
            return pd.DataFrame(columns=['measurement_date', 'measurement_value'])

        
        
        

if __name__ == "__main__":
    db = MySQLDatabase("localhost","3306","root","password","hospital_db")
    db.connect()
    print(db.get_data("100005546"))
