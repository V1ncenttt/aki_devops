#!/usr/bin/env python3

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

 # Simple one hidden layer network 
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

def train_preprocessing(training_filepath):
    """
        Preprocess input of the network. Runs on training data with AKI column.

        Arguments:
            - training_filepath {string} -- csv file path 
                

        Returns:
            - {torch.tensor} -- Preprocessed input array 
            - {torch.tensor}  -- Preprocessed target array 
            - {list} -- Expected columns based on the training data
              
        """
    
    # For the graded environment, this will be /data/training.csv
    df = pd.read_csv(training_filepath)
    
    
    # Encode 'aki' as numerical values if in training mode
    if 'aki' in df.columns:
        df['aki'] = df['aki'].apply(lambda x: 1 if x == 'y' else 0)
    
    # Encode 'sex' as numerical values (0 for male, 1 for female)
    if 'sex' in df.columns:
        df['sex'] = df['sex'].replace({'m': 0, 'f': 1})

    for col in df.columns:
        if 'creatinine_date' in col:
            df[col] = pd.to_datetime(df[col],format= '%m/%d/%y %H:%M:%S', errors='coerce')  # Transform strings to datetime

    y = df['aki'].values  # Extract labels
    
    # Extract the creatinine result column 
    creatinine_columns = [col for col in df.columns if 'creatinine_result' in col]
    
    df.fillna(0, inplace=True) # Fill null values with 0 

    
    # Add derived features: median and max creatinine values
    df['creatinine_median'] = df[creatinine_columns].median(axis=1)
    df['creatinine_max'] = df[creatinine_columns].max(axis=1)
    
    

    # Normalize 'age' between 0 and 1
    if 'age' in df.columns:
        df['age'] = df['age'] / 100
    
    df = df.drop(columns=['aki'])  # Drop label column and get features

    X = df.iloc[:, ::-1] # reverse so that most recent test results appear first (match with test processing)
    expected_columns = X.columns.tolist() # Collect column names based on training

    # Conversions
    X = X.to_numpy()  
    y = np.array(y) 
    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32).unsqueeze(1) 
    

    return X_tensor, y_tensor, expected_columns

def training(training_filepath):
    """
        Train model

        Arguments:
            - training_filepath {string} -- csv file path 
                

        Returns:
            - {SimpleNN(nn.Module)} -- Trained Model 
            - {list} -- Expected columns based on the training data
              
        """
    # Train based on training.csv (in grading it's '/data/training.csv')
    
    # Preprocess and create dataset
    X_tensor, y_tensor, expected_cols = train_preprocessing(training_filepath)
    dataset = TensorDataset(X_tensor, y_tensor)

    # Set random seed for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)

   

    # Hyperparameters
    input_size = X_tensor.shape[1]
    hidden_size = 64 
    learning_rate = 0.001
    batch_size = 16
    num_epochs = 20

    # Initialize 
    model = SimpleNN(input_size, hidden_size)
    criterion = nn.BCELoss()
    optimizer = optim.SGD(model.parameters(), lr=learning_rate)

    # Load 
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Training loop
    for epoch in range(num_epochs):
        all_predictions = []
        all_labels = []
        for batch_X, batch_y in dataloader:
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            # Collect predictions and labels
            predictions = (outputs > 0.3).int()  # Lower than usual because we care more about FN
            all_predictions.extend(predictions.numpy()) # Use extend to get a flat list
            all_labels.extend(batch_y.numpy())
            
            # Backward pass and optimization
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
 
        # Calculate F3 score for the epoch
        f3_score_training = fbeta_score(all_labels, all_predictions, beta=3, zero_division=1)
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}, F3 Score: {f3_score_training:.4f}')

    # Save the model
    torch.save(model.state_dict(), 'model.pth')
    
    
    # Save expected columns separately
    import json
    with open('expected_columns.json', 'w') as f:
        json.dump(expected_cols, f)  # Save as a JSON file

    return model, expected_cols # TODO: check this 


# Call function to train model
# TODO: Check how this should be coded 
# training('/data/training.csv')