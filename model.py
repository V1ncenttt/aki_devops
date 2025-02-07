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

    def __init__(self, predict_queue):
        """_summary_

        Args:
            
        """
        self.predict_queue = predict_queue
        with open('expected_columns.json', 'r') as f:
            self.expected_columns = json.load(f)
        self.expected_columns_len = len(self.expected_columns)  # Ensure we get the correct number of features
        self.model = SimpleNN(input_size=self.expected_columns_len, hidden_size=64)  # Match training definition
        self.model.load_state_dict(torch.load('model.pth', weights_only=True))  # Load trained weights
        self.model.eval()


        
    def test_preprocessing(self, measurement_row, expected_columns):
        """
            Preprocess input of the network. Runs on training data with AKI column.

            Arguments:
                - training_filepath {string} -- csv file path # TODO: CHANGE THIS DESCRIPTION
                - expected_columns {list} -- Expected columns based on the training data
                    

            Returns:
                - {torch.tensor}  -- Preprocessed input array 
                - {list} -- Expected labels (when using test.csv). 
                
            """
            
        
        # Using measurment row
        df = measurement_row
        
        
        # Make sure that mrn column is either dropped or not inputted! 
        if 'mrn' in df.columns:
            df = df.drop(columns=['mrn'])
        
        df['sex'] = df['sex'].map({'f': 0, 'm': 1})
        for col in df.columns:
            if 'creatinine_date' in col:
                df[col] = pd.to_datetime(df[col],format= '%m/%d/%y %H:%M:%S', errors='coerce')  # Convert to datetime

        # This is only used when running on personal environment, where test.csv includes ground truth labels.
        if 'aki' in df.columns:
            df['aki'] = df['aki'].map({'n': 0, 'y': 1}) # Convert to binary 
            y = df['aki'].values  # Extract labels
        else: y = 0
        
        # Fill nan values with 0
        df = df.apply(pd.to_numeric, errors='coerce')  # Convert all columns to numeric, replacing invalids with NaN
        df.fillna(0, inplace=True)
        
        # 🔹 Extract the same creatinine result columns as training
        creatinine_columns = [col for col in df.columns if 'creatinine_result' in col]
        
        # 🔹 Add derived features: median & max creatinine values 
        df['creatinine_median'] = df[creatinine_columns].median(axis=1)
        df['creatinine_max'] = df[creatinine_columns].max(axis=1)
        
        # Match test data size with training data size if it is larger 
        expected_columns_len = len(expected_columns)

        df_reversed = df.iloc[:, ::-1]  # Reverse column order so that mose recent test dates 
        
        df_reversed = df_reversed.iloc[:, :expected_columns_len]  # Keeps only the first `expected_columns_len` columns
        
        
        # Pad if test is smaller than training
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
        X_test, y = self.test_preprocessing(measurement_vector, self.expected_columns)
        
        
        
        self.model.eval
        with torch.no_grad():  
            predictions = self.model(X_test)

        predictions = predictions.detach().numpy()
        logging.info(f"prediction: {predictions}")
        
        # Convert to binary
        return int((predictions.item()) > 0.3) # Lower than usual because we care more about F3 
        
    def run(self):
        (mrn, test_time, patient_vector) = self.predict_queue.pop(0) # THIS IS SUPER INEFFICIENT LATER CHANGE USEAGE OF TYPE OF QUEUE FOR SPEED
        if self.predict_aki(patient_vector):
            return (mrn, test_time)
        else:
            return None


if __name__=="__main__":
    from sklearn.metrics import fbeta_score
    dummy_queue = []
    model = Model(dummy_queue)
     
    # EXTRACT GROUND TRUTH VALUES FROM TEST.CSV!!!!
    # Load test dataset
    df = pd.read_csv("test.csv")
    # Extract true AKI labels and convert 'y' to 1, 'n' to 0
    aki_data = np.where(df['aki'] == 'y', 1, 0).astype(int)

    # Save as CSV without column name
    #np.savetxt("aki_labels.csv", aki_data, fmt='%d', delimiter=',')

    # Run model prediction on the test dataset
    predictions = []
    for i in range(len(df)):
        print(f"Progress: {i+1:03d}/{len(df)}")
        row = df.iloc[[i]].copy()
        prediction = model.predict_aki(row)
        predictions.append(prediction)

    # Load saved labels without headers
    #data = np.loadtxt('aki_labels.csv', delimiter=',', dtype=int)

    # Compute F3 Score
    f3_score_test = fbeta_score(aki_data, predictions, beta=3, zero_division=1)

    print('Final F3 score:', f3_score_test)