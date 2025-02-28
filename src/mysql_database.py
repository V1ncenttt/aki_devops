"""
MySQL Database Module for Patient & Measurement Data

This module defines a MySQL database interface using SQLAlchemy ORM to manage patient records 
and their associated creatinine measurements. It supports inserting, updating, and retrieving 
data in a structured format.

Classes:
    - Patient: SQLAlchemy model for storing patient demographic data.
    - Measurement: SQLAlchemy model for storing creatinine measurement data.
    - MySQLDatabase: Handles database connection, CRUD operations, and data retrieval.

Usage Example:
    db = MySQLDatabase("localhost", "3306", "root", "password", "hospital_db")
    db.connect()
    db.add_patient('12345', 25, 'M')
    db.add_measurement('12345', 1.1)
    patient_data = db.get_data('12345')
    db.disconnect()

Dependencies:
    - SQLAlchemy for ORM operations.
    - Pandas for data processing.
    - Logging for error handling.

Authors:
    - Vincent Lefeuve (vincent.lefeuve24@ic.ac.uk)
    - Alison Lupton (alison.lupton24@ic.ac.uk)
"""

from datetime import datetime, timezone
import time
import logging
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    Enum,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base  # Safer, automatic sanitizing
from sqlalchemy.dialects.mysql import insert
import pandas as pd
from src.database import Database
from pymysql.err import OperationalError

Base = declarative_base()


class Patient(Base):
    """
    Represents a patient record in the database.

    Attributes:
        mrn (str): Medical record number (Primary Key).
        age (int, optional): Age of the patient.
        sex (str, optional): Gender of the patient ('M', 'F', 'Other').
    """

    __tablename__ = "Patients"
    mrn = Column(String(50), primary_key=True)
    age = Column(Integer, nullable=True)
    sex = Column(Enum("M", "F", "Other"), nullable=True)


class Measurement(Base):
    """
    Represents a creatinine measurement record in the database.

    Attributes:
        mrn (str): Foreign key linking to Patient.mrn.
        creatinine_date (datetime): Timestamp of the measurement (Primary Key).
        creatinine_result (float): Measured creatinine level.
    """

    __tablename__ = "Measurements"
    mrn = Column(
        String(50), ForeignKey("Patients.mrn", ondelete="CASCADE"), primary_key=True
    )
    creatinine_date = Column(DateTime, primary_key=True, default=datetime.now())
    creatinine_result = Column(Float, nullable=False)


class MySQLDatabase(Database):
    """
    Interface for interacting with a MySQL database using SQLAlchemy ORM.

    Methods:
        - connect(): Establishes a database connection.
        - disconnect(): Closes the database connection.
        - add_patient(): Inserts or updates a patient record.
        - add_measurement(): Inserts or updates a creatinine measurement.
        - get_data(): Retrieves historical creatinine measurements for a given patient.
    """

    def __init__(self, host, port, user, password, db):
        """
        Initializes the MySQLDatabase instance and establishes a database connection.

        Args:
            host (str): Database hostname or IP address.
            port (str): Database port number.
            user (str): Username for authentication.
            password (str): Password for authentication.
            db (str): Database name.
        """
        database_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"

        try:
            self.engine = create_engine(database_uri, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            logging.info("mysql_database.py: MySQL database object created.")
        except (SQLAlchemyError, OperationalError) as e:
            logging.error(
                f"mysql_database.py: Error initializing database connection: {e}"
            )

    def connect(self, delay=1, max_attempts=-1) -> bool:
        """
        Opens a new session with the database. Retries indefinitely until successful.
        Returns True if connection is successful, False otherwise.
        """
        attempt = 0
        while attempt != max_attempts:
            logging.info(
                f"mysql_database.py: Connecting to MySQL database... (attempt {attempt + 1})"
            )
            try:
                if hasattr(self, "session") and self.session is not None:
                    self.session.close()  # Close any existing session

                self.engine.dispose()  # Dispose of old connections
                self.session = self.Session()
                # Check if connection is successful
                self.session.execute(text("SELECT 1"))  # Sample check query
                logging.info("mysql_database.py: Connected to MySQL database.")
                return True

            except (SQLAlchemyError, OperationalError) as e:
                logging.error(
                    f"mysql_database.py: Database connection failed (attempt {attempt + 1}): {e}"
                )
                attempt += 1
                time.sleep(delay)
                delay *= 1.5

        return False

    def disconnect(self):
        """
        Closes the current session with the database.
        """
        self.session.close()
        logging.info("mysql_database.py: Disconnected from MySQL database.")

    def add_patient(
        self, mrn: str, age: int = None, sex: str = None, max_attempts=2
    ) -> bool:
        """
        Adds a new patient or updates an existing one.

        Args:
            mrn (str): Medical record number.
            age (int, optional): Age of the patient.
            sex (str, optional): Gender of the patient ('M', 'F', 'Other').

        Returns:
            bool: True if patient was added successfully,
        """
        attempt = 0

        while attempt != max_attempts:
            try:
                logging.info(
                    f"mysql_database.py: Adding patient with MRN {mrn}... (attempt {attempt + 1})"
                )
                stmt = insert(Patient).values(mrn=mrn, age=age, sex=sex)
                stmt = stmt.on_duplicate_key_update(
                    age=stmt.inserted.age, sex=stmt.inserted.sex
                )
                self.session.execute(stmt)
                self.session.commit()

                logging.info(f"mysql_database.py: Added patient with MRN {mrn}.")
                return True

            except (SQLAlchemyError, OperationalError) as e:
                attempt += 1
                logging.error(
                    f"mysql_database.py: Error adding patient, will try reconnecting to the database: {e}"
                )

                connected = self.connect(max_attempts=3)

                if not connected and attempt == max_attempts - 1:
                    logging.error(
                        f"mysql_database.py: Failed to connect to database. Aborting."
                    )
                    return False

    def add_measurement(
        self, mrn: str, creatinine_result: float, creatinine_date=None, max_attemps=2
    ) -> bool:
        """
        Adds a new creatinine measurement for a patient.

        Args:
            mrn (str): Medical record number.
            creatinine_result (float): Measured creatinine value.
            creatinine_date (datetime, optional): Timestamp of the measurement.
        """
        attempt = 0

        while attempt != max_attemps:
            try:
                logging.info(
                    f"mysql_database.py: Adding measurement for MRN {mrn}... (attempt {attempt + 1})"
                )

                creatinine_date = creatinine_date or datetime.now(timezone.utc)
                stmt = insert(Measurement).values(
                    mrn=mrn,
                    creatinine_result=creatinine_result,
                    creatinine_date=creatinine_date,
                )
                stmt = stmt.on_duplicate_key_update(
                    creatinine_result=stmt.inserted.creatinine_result
                )

                self.session.execute(stmt)
                self.session.commit()

                logging.info(f"mysql_database.py: Added measurement for MRN {mrn}.")

                return True

            except (SQLAlchemyError, OperationalError) as e:
                attempt += 1
                logging.error(
                    f"mysql_database.py: Error adding measurement, will try reconnecting to the database: {e}"
                )

                connected = self.connect(max_attempts=3)

                if not connected and attempt == max_attemps - 1:
                    logging.error(
                        f"mysql_database.py: Failed to connect to database. Aborting."
                    )
                    return False

        return False

    def get_data(self, mrn: str, max_attempts=2) -> tuple[bool, pd.DataFrame]:
        """
        Retrieves historical creatinine measurements  and demographics for a given patient as a pandas DataFrame.

        Args:
            mrn (str): Medical record number (MRN) of the patient.

        Returns:
            DataFrame: DataFrame with columns ['creatinine_date', 'creatinine_result'] sorted by date.
        """

        attempt = 0

        while attempt != max_attempts:

            try:
                # Query both tables to get measurements and  patient info
                logging.info(
                    f"mysql_database.py: Retrieving data for MRN {mrn}... (attempt {attempt + 1})"
                )
                patient_data = (
                    self.session.query(Patient.age, Patient.sex)
                    .filter_by(mrn=mrn)
                    .first()
                )
                if not patient_data:
                    logging.warning(
                        f"mysql_database.py: No patient found for MRN {mrn}"
                    )
                    return None  # empty df if patient doesn't exist (I don't think this should happen)

                age, sex = patient_data.age, patient_data.sex
                measurements = (
                    self.session.query(
                        Measurement.creatinine_date, Measurement.creatinine_result
                    )
                    .filter_by(mrn=mrn)
                    .order_by(Measurement.creatinine_date.asc())
                    .all()
                )

                # Convert results to DataFrame
                df = pd.DataFrame(
                    measurements, columns=["creatinine_date", "creatinine_result"]
                )

                # Ensure datetime format for processing
                df["creatinine_date"] = pd.to_datetime(
                    df["creatinine_date"], errors="coerce"
                )

                # Convert to Feature Vector (Flatten)
                flattened_features = {
                    "age": age,
                    "sex": sex,
                }

                # Convert measurement history to columns like creatinine_date_0, creatinine_result_0, etc.
                for i, row in df.iterrows():
                    flattened_features[f"creatinine_date_{i}"] = row["creatinine_date"]
                    flattened_features[f"creatinine_result_{i}"] = row[
                        "creatinine_result"
                    ]

                # Convert to DataFrame (Single Row)
                feature_df = pd.DataFrame([flattened_features])

                logging.info(f"mysql_database.py: Retrieved data for MRN {mrn}.")
                return (True, feature_df)

            except (SQLAlchemyError, OperationalError) as e:
                attempt += 1
                logging.error(
                    f"Error retrieving data for MRN {mrn}, will try reconnecting to the database: {e}"
                )

                connected = self.connect(max_attempts=3)

                if not connected and attempt == max_attempts - 1:
                    logging.error(
                        f"mysql_database.py: Failed to connect to database. Aborting."
                    )
                    return (False, None)

        return (False, None)


if __name__ == "__main__":

    # Reliability tests - Duplicate handling logic
    db = MySQLDatabase("localhost", "3306", "root", "password", "hospital_db")
    db.connect()
    db.add_patient("12345", 22, "M")

    db.get_data("12345")
    db.add_patient("12345", 23, "M")
    db.get_data("12345")

    # Test measurements
    sample_datetime = datetime.now()
    db.add_measurement("12345", 1.1, sample_datetime)
    db.get_data("12345")
    db.add_measurement("12345", 1.2, sample_datetime)
    db.get_data("12345")
