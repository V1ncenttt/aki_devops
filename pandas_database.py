import pandas as pd
import logging
from database import Database

class PandasDatabase(Database):
    """Manages patient data using a Pandas DataFrame with MRN as the index."""

    def __init__(self, filename):
        """Initialize the database from a CSV file."""
        self.filename = filename  # Save filename for persistence

        # Load CSV
        try:
            self.df = pd.read_csv(filename)
        except FileNotFoundError:
            logging.warning(f"File {filename} not found, creating a new database.")
            self.df = pd.DataFrame(columns=["mrn", "age", "sex"])

        # Ensure MRN is the index
        if "mrn" in self.df.columns:
            self.df.set_index("mrn", inplace=True)

        # Ensure required columns exist
        self.ensure_columns()
        
        logging.info("Database initialized.")

    def ensure_columns(self):
        """Ensure all required columns (age, sex, 43 measurement slots) exist."""
        required_columns = ["age", "sex"] + [f"creatinine_date_{i}" for i in range(44)] + [f"creatinine_result_{i}" for i in range(44)]

        for col in required_columns:
            if col not in self.df.columns:
                self.df[col] = None  # Initialize missing columns with None

        # Make age then sex the first two columns
        self.df = self.df[["age", "sex"] + [col for col in self.df.columns if col not in ["age","sex"]]]
        
        self.df.fillna(0, inplace=True)  # Fill NaNs with 0


    def get_data(self, mrn):
        """Return the patient row for a given MRN."""
        if mrn in self.df.index:
            return self.df.loc[mrn].copy()
        else:
            return pd.DataFrame(columns=self.df.columns)  # Return an empty row structure

    def add_patient(self, mrn, age=None, sex=None):
        """Add a new patient or update an existing one."""
        if mrn in self.df.index:
            # Update existing patient
            self.df.at[mrn, "age"] = age
            self.df.at[mrn, "sex"] = sex
        else:
            # Create new patient row
            new_row = pd.DataFrame([[age, sex] + [0] * 88], columns=self.df.columns, index=[mrn])
            self.df = pd.concat([self.df, new_row])

        #self.save()

    def add_measurement(self, mrn, measurement, test_date):
        """Add a new creatinine measurement for a patient."""
        if mrn not in self.df.index:
            # Create a new row if the patient does not exist
            new_row = pd.DataFrame([[0, 0] + [0] * 86], columns=self.df.columns, index=[mrn])
            self.df = pd.concat([self.df, new_row])

        # Get patient row
        patient_data = self.df.loc[mrn]

        # Find the first available empty slot
        for i in range(44):
            date_col = f"creatinine_date_{i}"
            result_col = f"creatinine_result_{i}"

            if patient_data[date_col] == 0:  # Empty slot found
                self.df.at[mrn, date_col] = test_date
                self.df.at[mrn, result_col] = measurement
                break

        #self.save()
