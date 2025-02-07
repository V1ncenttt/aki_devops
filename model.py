"""_summary_
"""

# Imports
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json 
from pandas_database import PandasDatabase
import logging
from database import Database

pd.set_option('future.no_silent_downcasting', True)
######################################

class SimpleNN(nn.Module):
        def __init__(self, input_size, hidden_size):
            super(SimpleNN, self).__init__()
            self.hidden = nn.Linear(input_size, hidden_size)
            self.activation_hidden = nn.ReLU()  # ReLU for hidden layer
            self.output = nn.Linear(hidden_size, 1)
            self.activation_output = nn.Sigmoid() # Sigmoid for binary classification

        def forward(self, x):
            x = self.activation_hidden(self.hidden(x))
            x = self.activation_output(self.output(x))
            return x

class Model:
    """_summary_"""

    def __init__(self, database: Database):
        """_summary_

        Args:
            database (_type_): _description_
        """
        self.database = PandasDatabase('history.csv') #TODO: Change it later to be out of this and set in main
        with open('expected_columns.json', 'r') as f:
            self.expected_columns = json.load(f)
        
        self.expected_columns_len = len(self.expected_columns)  # Ensure we get the correct number of features
        self.model = SimpleNN(input_size=self.expected_columns_len, hidden_size=64)  # Match training definition
        self.model.load_state_dict(torch.load('model.pth', weights_only=True))  # Load trained weights
        self.model.eval()
        self.last_df = None

    def add_measurement(self, mrn, measurement, test_date):
        """_summary_

        Args:
            mrn (_type_): _description_
            measurement (_type_): _description_
            test_date (_type_): _description_
        """
        return self.database.add_measurement(mrn, measurement, test_date)
    
    def get_past_measurements(self, mrn, creatinine_value, test_time):
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
        
        logging.info(patient_vector.shape)
        return patient_vector
    
    def add_patient(self, mrn, age=None, sex=None):
        """_summary_

        Args:
            mrn (_type_): _description_
            age (_type_, optional): _description_. Defaults to None.
        """
        return self.database.add_patient(mrn, age,sex)
        
        
    def test_preprocessing(self, measurement_row, expected_columns):
        """
            Preprocess input of the network. Runs on training data with AKI column.

            Arguments:
                - training_filepath {string} -- csv file path
                - expected_columns {list} -- Expected columns based on the training data
                    

            Returns:
                - {torch.tensor}  -- Preprocessed input array 
                - {list} -- Expected labels (when using test.csv). 
                
            """
            
        
        # Using measurment row
        df = measurement_row
        
        #logging.info(f"measurement_row: {df}")
        
        # Make sure that mrn column is either dropped or not inputted! 
        if 'mrn' in df.columns:
            df = df.drop(columns=['mrn'])
        
        df['sex'] = df['sex'].map({'M': 0, 'F': 1})
        df['age'] = df['age'] / 100  # Normalize age

        for col in df.columns:
            if 'creatinine_date' in col:
                df[col] = 0  # Convert to 0 for now
               


        
        # Convert to numeric
        #df = df.apply(pd.to_numeric, errors='coerce')
        df.fillna(0, inplace=True)
        
        
        # 🔹 Extract the same creatinine result columns as training
        creatinine_columns = [col for col in df.columns if 'creatinine_result' in col]
        
        # 🔹 Add derived features: median & max creatinine values 
        df['creatinine_median'] = df[creatinine_columns].median(axis=1)
        df['creatinine_max'] = df[creatinine_columns].max(axis=1)
                
        X = df.iloc[:, ::-1] # Reverse so that most recent test results appear first (match with test processing)
        #X_tensor = torch.tensor(X, dtype=torch.float32)
        #Convert all to float
        X = X.astype(float)
        X_tensor = torch.tensor(X.to_numpy(), dtype=torch.float32)
        


        return X_tensor
    
    def predict_aki(self, measurement_vector):

        """
         Args:
            mrn (_type_): _description_
            measurements (_type_): _description_

        Returns:
            _type_: _description_
        Use a trained model to create label predictions on input data  

        Arguments:
            - filepath {string} -- csv training path
            - model -- Trained model
            - expected_columns {list} -- Expected columns based on the training data
                

        Returns:
            - {numpy array}  -- predictions
            - {list}  -- Expected labels (when we have a ground truth). 
              
            """
        # Preprocess then run on trained model 
        X_test = self.test_preprocessing(measurement_vector, self.expected_columns)
        
        
        
        self.model.eval
        with torch.no_grad():  
            predictions = self.model(X_test)

        predictions = predictions.detach().numpy()
        logging.info(f"prediction: {predictions}")
        
        # Convert to binary
        return (predictions > 0.3).astype(int) # Lower than usual because we care more about F3 
        
        
        
  

