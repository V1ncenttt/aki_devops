"""
blablabla
"""
import csv
from collections import defaultdict
import asyncio
import pandas as pd

class PandasDatabase:
    """_summary_
    """
    def __init__(self, filename):
        """_summary_

        Args:
            filename (_type_): _description_
        """

        self.df = pd.read_csv(filename)
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
        
    async def get_past_measurements(self, mrn, creatinine_value, test_time):
        """_summary_

        Args:
            mrn (_type_): _description_

        Returns:
            _type_: _description_
        """
        patient_vector = self.database.get_data(mrn)

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
            
        patient_data =  self.df[self.df['mrn'] == mrn]
        return patient_data # TODO: Default values??

        
    def add_patient(self, mrn, age=None, sex=None):
        """_summary_

        Args:
            mrn (_type_): _description_
            age (_type_, optional): _description_. Defaults to None.
        """
        
            
        # Check if patien already is in the system 
        if mrn in self.df["mrn"].values:

            self.df.loc[self.df["mrn"] == mrn, "age"] = age
            self.df.loc[self.df["mrn"] == mrn, "sex"] = sex
        else:
            # Create new row 
            new_row = {"mrn": mrn, "age": age, "sex": sex}
            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            
                


        
        
    def add_measurement(self, mrn, measurement, test_date):
        """_summary_

        Args:
            mrn (_type_): _description_
            data (_type_): _description_
        """
        
    
        ### FIND LAST INDEX USED
        # Find the last used creatinine_date column
        patient_data =  self.df[self.df.iloc['mrn'] == mrn]
        date_cols = [col for col in patient_data if "creatinine_date" in col]
        last_used_n = -1  # Default if no columns exist
        
        for col in date_cols:
            n = int(col.split("_")[-1])  # Extract the number from creatinine_date_n
            if pd.notna(self.df.at[mrn, col]):  # Check if it has a value
                last_used_n = max(last_used_n, n)
                
        # Next available index
        next_n = last_used_n + 1

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



   