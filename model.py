"""_summary_
"""

# Imports
import argparse
import csv
import random
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.metrics import fbeta_score  
from train_model_script import SimpleNN 
import json 

######################################
class Model:
    """_summary_"""

    def __init__(self, database):
        """_summary_

        Args:
            database (_type_): _description_
        """
        self.database = database
        self.filepath = '.csv' #TODO: fix this from parser  
        with open('expected_columns.json', 'r') as f:
            self.expected_columns = json.load(f)
        
        self.expected_columns_len = len(self.expected_columns)  # Ensure we get the correct number of features
        self.model = SimpleNN(input_size=self.expected_columns_len, hidden_size=64)  # Match training definition
        self.model.load_state_dict(torch.load('model.pth'))  # Load trained weights

    def create_tensor_from_measurements(self, measurements):
        """_summary_

        Args:
            measurements (_type_): _description_

        Returns:
            _type_: _description_
        """
        return NotImplementedError

    async def add_measurement(self, mrn, measurement, test_date):
        """_summary_

        Args:
            mrn (_type_): _description_
            measurement (_type_): _description_
            test_date (_type_): _description_
        """
        return self.database.add_data(mrn, (measurement, test_date))
    
    async def get_past_measurements(self, mrn, creatinine_value, test_time):
        """_summary_

        Args:
            mrn (_type_): _description_

        Returns:
            _type_: _description_
        """
        patient_vector = self.database.get_data(mrn)
        patient_vector += [test_time, creatinine_value]

        #Pad with 0s if needed
        #TODO: use your preprocessing method
        if len(patient_vector) < self.expected_columns_len:
            patient_vector += [0] * (self.expected_columns_len - len(patient_vector))
        #Convert to tensor
        return torch.tensor(patient_vector, dtype=torch.float32)
    
    def add_patient(self, mrn, age=None, sex=None):
        """_summary_

        Args:
            mrn (_type_): _description_
            age (_type_, optional): _description_. Defaults to None.
        """
        return self.database.add_patient(mrn, age,sex)
        
        
    def test_preprocessing(self, filepath, expected_columns):
        """
            Preprocess input of the network. Runs on training data with AKI column.

            Arguments:
                - training_filepath {string} -- csv file path
                - expected_columns {list} -- Expected columns based on the training data
                    

            Returns:
                - {torch.tensor}  -- Preprocessed input array 
                - {list} -- Expected labels (when using test.csv). 
                
            """
        # Filepath should be test.csv (the input)
        df = pd.read_csv(filepath)

        
        df['sex'] = df['sex'].map({'f': 0, 'm': 1})
        for col in df.columns:
            if 'creatinine_date' in col:
                df[col] = pd.to_datetime(df[col],format= '%m/%d/%y %H:%M:%S', errors='coerce')  # Convert to datetime

        # This is only used when running on personal environment, where test.csv includes labels.
        if 'aki' in df.columns:
            df['aki'] = df['aki'].map({'n': 0, 'y': 1}) # Convert to binary 
            y = df['aki'].values  # Extract labels
        else: y = 0
        
        # Fill nan values with 0
        df.fillna(0, inplace=True)
        
        # 🔹 Extract the same creatinine result columns as training
        creatinine_columns = [col for col in df.columns if 'creatinine_result' in col]
        
        # 🔹 **Add derived features: median & max creatinine values**
        df['creatinine_median'] = df[creatinine_columns].median(axis=1)
        df['creatinine_max'] = df[creatinine_columns].max(axis=1)
        
        # Match test data size with training data size if it is larger 
        expected_columns_len = len(expected_columns)

        df_reversed = df.iloc[:, ::-1]  # Reverse column order so that mose recent test dates 
        
        df_reversed = df_reversed.iloc[:, :expected_columns_len]  # Keeps only the first `expected_columns_len` columns
        
        
        # Pad if test is smaller than training!!! 
        for col in expected_columns:
            if col not in df.columns:
                df[col] = 0  # pad with 0
        df = df[expected_columns]
        
        
        # Convert to tensors
        X = df_reversed

        X = X.to_numpy()  
        y = np.array(y) 
        X_tensor = torch.tensor(X, dtype=torch.float32)
        X_tensor = torch.tensor(df.to_numpy(), dtype=torch.float32)


        return X_tensor, y

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
        X_test, y = self.test_preprocessing(self.filepath, self.expected_columns)
        
        
        
        self.model.eval
        with torch.no_grad():  
            predictions = self.model(X_test)

        predictions = predictions.detach().numpy()
        
        # Convert to binary
        return (predictions > 0.3).astype(int) # Lower than usual because we care more about FN 
        #TODO: check this 
        
        
  

