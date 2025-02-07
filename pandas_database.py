"""
Pandas Database Module
======================
This module provides the `PandasDatabase` class, which extends the `Database` class to store and process patient 
data using pandas DataFrames. It supports data retrieval, historical processing, and adding new measurements.

Authors:
--------
- Kerim Birgi (kerim.birgi24@imperial.ac.uk)
- Alsion Lupton (alison.lupton24@imperial.ac.uk)

Classes:
--------
- `PandasDatabase`: Handles patient data storage and processing using pandas.

Usage:
------
Example:
    db = PandasDatabase("patients.csv")
    patient_data = db.get_data(12345)
    db.add_measurement(12345, 1.2, "2025-02-07 12:30:00")

"""

import csv
from collections import defaultdict
from database import Database
import pandas as pd


class PandasDatabase(Database):
    """
    Pandas-based Implementation of the Database
    ============================================
    Stores patient records, processes historical data, and updates measurements.

    Attributes:
    -----------
    - `df (DataFrame)`: Stores patient data with MRN as index.
    """

    def __init__(self, filename):
        """
        Initializes the PandasDatabase with a patient dataset.
        
        Args:
            filename (str): Path to the CSV file containing patient data.
        """

        self.df = pd.read_csv(filename, date_format="%m/%d/%y %H:%M:%S")
        self.df.set_index("mrn", inplace=True)  # Set MRN as the index

        # Add empty 'age' and 'sex' columns
        self.df.insert(1, "age", None)
        self.df.insert(2, "sex", None)

    def history_preprocessing(self):  # TODO: Delete the function
        """
        Converts date columns to datetime format for easier processing.
        """

        for col in self.df.columns:
            if "creatinine_date" in col:
                self.df[col] = pd.to_datetime(
                    self.df[col], format="%m/%d/%y %H:%M:%S", errors="coerce"
                )  # Transform strings to datetime


    def get_past_measurements(self, mrn, creatinine_value, test_time):
        """
        Retrieves historical creatinine measurements for a given patient and appends the new test.
        
        Args:
            mrn (int): Patient's medical record number.
            creatinine_value (float): New creatinine measurement.
            test_time (str): Timestamp of the new measurement.
        
        Returns:
            DataFrame: Updated patient data with the new measurement.
        """
        patient_vector = self.get_data(mrn)

        if patient_vector is None or patient_vector.empty:
            return None  # Handle case where patient does not exist

        # Convert Series to DataFrame
        if isinstance(patient_vector, pd.Series):
            patient_vector = patient_vector.to_frame().T  # Convert to DataFrame


        ### FIND LAST INDEX USED
        # Find the last used creatinine_date column

        date_cols = [
            col
            for col in patient_vector.columns
            if isinstance(col, str) and "creatinine_date" in col
        ]

        last_used_n = -1  # Default if no columns exist

        for col in date_cols:
            n = int(col.split("_")[-1])  # Extract the number from creatinine_date_n
            # print(patient_vector[col])
            if not patient_vector[col].isna().all():  # Check if it has a value
                last_used_n = max(last_used_n, n)

        # Next available index
        next_n = last_used_n + 1

        # Column names for the new test
        new_date_col = f"creatinine_date_{next_n}"
        new_result_col = f"creatinine_result_{next_n}"

        # Append the new measurement to the patient vector does NOT modify the dataframe
        patient_vector[new_date_col] = test_time
        patient_vector[new_result_col] = creatinine_value

        # Convert to tensor
        return patient_vector

    def get_data(self, mrn):
        """
        Retrieves a patient's data by MRN.
        
        Args:
            mrn (int): Patient's medical record number.
        
        Returns:
            DataFrame: Patient's data if found, else an empty DataFrame.
        """

        # Returns df row
        if mrn in self.df.index:  # check to see if patient exists
            patient_data = self.df.loc[[mrn]].copy()
            return patient_data
        else:
            return pd.DataFrame(
                columns=self.df.columns
            )  # initialise and return empty dataframe

    def add_patient(self, mrn, age=None, sex=None):
        """
        Adds a new patient entry or updates an existing one.
        
        Args:
            mrn (int): Patient's medical record number.
            age (int, optional): Patient's age.
            sex (str, optional): Patient's sex.
        """

        # Check if patient already is in the system
        if mrn in self.df.index:

            self.df.at[mrn, "age"] = age
            self.df.at[mrn, "sex"] = sex
        else:
            # Create new row
            new_row = pd.DataFrame([[age, sex]], index=[mrn], columns=["age", "sex"])
            self.df = pd.concat([self.df, new_row])

    def add_measurement(self, mrn, measurement, test_date):
        """
        Adds a new creatinine measurement for a patient.
        
        Args:
            mrn (int): Patient's medical record number.
            measurement (float): New creatinine measurement.
            test_date (str): Timestamp of the measurement.
        """

        # Check if the patient row exists, otherwise create it ( we shouldn't have to do this currently)
        if mrn not in self.df.index:
            new_row = pd.DataFrame(
                [[None] * len(self.df.columns)], columns=self.df.columns, index=[mrn]
            )
            self.df = pd.concat([self.df, new_row])

        # Get patient data
        patient_data = self.df.loc[mrn]

        # Find the existing "creatinine_date" columns
        date_cols = sorted(
            [col for col in self.df.columns if "creatinine_date" in col],
            key=lambda x: int(x.split("_")[-1]),
        )  # Sort by index number

        last_used_n = -1  # Default if no columns exist
        empty_col = None  # Store first empty column if available

        for col in date_cols:
            n = int(col.split("_")[-1])  # Extract index number

            if pd.isna(patient_data[col]):  # Check if this column is empty
                empty_col = n
                break  # Stop at the first available empty column
            else:
                last_used_n = max(last_used_n, n)  # Keep track of the last used index

        # Decide which column to use
        if empty_col is not None:
            next_n = empty_col  # Use first available empty slot
        else:
            next_n = (
                last_used_n + 1
            )  # Create a new column if no empty slot found (edits df)

        # Column names for the new test
        new_date_col = f"creatinine_date_{next_n}"
        new_result_col = f"creatinine_result_{next_n}"

        # If the columns do not exist, add them dynamically
        if new_date_col not in self.df.columns:
            self.df[new_date_col] = None
            self.df[new_result_col] = None

        # Update the DataFrame with new values
        self.df.at[mrn, new_date_col] = test_date
        self.df.at[mrn, new_result_col] = measurement
