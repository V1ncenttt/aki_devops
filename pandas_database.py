"""
blablabla
"""
import csv
from collections import defaultdict
from database import Database
import pandas as pd

class PandasDatabase(Database):
    """_summary_
    """
    def __init__(self, filename):
        """_summary_

        Args:
            filename (_type_): _description_
        """

        self.df = pd.read_csv(filename)
        self.df.set_index("mrn", inplace=True) # Set MRN as the index 
        self.history_preprocessing()
        
        # Add empty 'age' and 'sex' columns
        self.df.insert(1, "age", None)
        self.df.insert(2, "sex", None)

 

    def history_preprocessing(self):
        """
            Populates our database with the hisotrical values (uses history.csv)

            Arguments:
                - training_filepath {string} -- csv file path 
                    

            Returns:
                - {torch.tensor} -- Preprocessed input array 
                - {torch.tensor}  -- Preprocessed target array 
                - {list} -- Expected columns based on the training data
                
            """
        
        for col in self.df.columns:
            if 'creatinine_date' in col:
                self.df[col] = pd.to_datetime(self.df[col],format= '%m/%d/%y %H:%M:%S', errors='coerce')  # Transform strings to datetime


        # TODO: should we still do this??
        # df.fillna(0, inplace=True) # Fill null values with 0 
        
    def get_past_measurements(self, mrn, creatinine_value, test_time):
        """_summary_

        Args:
            mrn (_type_): _description_

        Returns:
            _type_: _description_
        """
        patient_vector = self.get_data(mrn)

        if patient_vector is None or patient_vector.empty:
            # print(f"[WARNING] Patient {mrn} not found in database. Creating a new entry.")
            return None  # Handle case where patient does not exist
        
        
        # Convert Series to DataFrame if needed
        if isinstance(patient_vector, pd.Series):
            patient_vector = patient_vector.to_frame().T  # Convert to DataFrame

        # print(patient_vector)  # Debugging print to verify it is a DataFrame

        ### FIND LAST INDEX USED
        # Find the last used creatinine_date column
        
        date_cols = [col for col in patient_vector.columns if isinstance(col, str) and "creatinine_date" in col]

        
        last_used_n = -1  # Default if no columns exist
        
        for col in date_cols:
            n = int(col.split("_")[-1])  # Extract the number from creatinine_date_n
            # print(patient_vector[col])
            if not patient_vector[col].isna().all(): # Check if it has a value
                last_used_n = max(last_used_n, n)
                
        # Next available index
        next_n = last_used_n + 1

        # Column names for the new test
        new_date_col = f"creatinine_date_{next_n}"
        new_result_col = f"creatinine_result_{next_n}"


        # Append the new measurement to the patient vector does NOT modify the dataframe
        patient_vector[new_date_col] = test_time
        patient_vector[new_result_col] = creatinine_value
        
        
        #Convert to tensor
        return patient_vector
    

    def get_data(self, mrn):
        """_summary_

        Args:
            mrn (int): A patients MRN number  

        Returns:
            _type_: _description_
        """
        
        # Returns df row 
        if mrn in self.df.index: # check to see if patient exists
            patient_data  = self.df.loc[[mrn]].copy()
            return patient_data
        else:
            return pd.DataFrame(columns = self.df.columns) #initialise and return empty dataframe
        

    
    def add_patient(self, mrn, age=None, sex=None):
        """_summary_

        Args:
            mrn (_type_): _description_
            age (_type_, optional): _description_. Defaults to None.
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
        """Add a new creatinine measurement for a patient."""
        
        # Check if the patient row exists, otherwise create it ( we shouldn't have to do this currently)
        if mrn not in self.df.index:
            new_row = pd.DataFrame([[None] * len(self.df.columns)], columns=self.df.columns, index=[mrn])
            self.df = pd.concat([self.df, new_row])

        # Get patient data
        patient_data = self.df.loc[mrn]

        # Find the existing "creatinine_date" columns
        date_cols = sorted([col for col in self.df.columns if "creatinine_date" in col], 
                        key=lambda x: int(x.split("_")[-1]))  # Sort by index number

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
            next_n = last_used_n + 1  # Create a new column if no empty slot found (edits df)

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
