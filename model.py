"""_summary_
"""

# Imports
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from joblib import dump, load
#from xgboost import XGBClassifier
import numpy as np
import json 
from pandas_database import PandasDatabase
import logging
from database import Database
from sklearn.preprocessing import LabelEncoder



class Model:
    """_summary_"""

    def __init__(self, predict_queue):
        self.predict_queue = predict_queue
        self.aki_model = load('aki_detection.joblib')
        self.le = LabelEncoder()


    def add_padding(self, df):
        """
        Add padding to dataframe to ensure constant length
        
        Args:
            df (Dataframe): Dataframe to be formatted

        Returns:
            Dataframe : Dataframe with constant measurement length of 50
        """
        for i in range(((len(df.columns)-2)//2), 50):
            df[f'creatinine_date_{i}'] = 0
            df[f'creatinine_result_{i}'] = 0
        return df
    
    def process_dates(self, df):
        """
        Process dates from the format of 'Year-Month-Day Hour-Minutes-Seconds' into seconds.
        0 is the time of the first measurement and all following values are in relation to the first measurement.
        
        Args:
            df (Dataframe): Dataframe with dates in 'Year-Month-Day Hour-Minutes-Seconds' format

        Returns:
            Dataframe : Dataframe with dates in seconds (int)
        """
        date_cols = [col for col in df.columns if "creatinine_date" in col]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        df['ref_date'] = df[date_cols].min(axis=1)
        for col in date_cols:
            df[col] = (df[col] - df['ref_date']).dt.total_seconds()
        df = df.drop(columns=['ref_date'])
        df = df.fillna(0)
        return df

    def process_features(self, df):
        """
        Process features of input data for detection of aki. First the dates are turned into seconds (int) and then padding is added to ensure constant length
        of input data. Finally some extra aggregated feature values are computed.

        Args:
            df (Dataframe): Dataframe with input data

        Returns:
            Dataframe : Dataframe with processed features
        """
        results_cols = [col for col in df.columns if "creatinine_result" in col]

        #df = self.process_dates(df)
        #df = self.add_padding(df)


        df['creatinine_mean'] = df[results_cols].mean(axis=1)
        df['creatinine_median'] = df[results_cols].median(axis=1, skipna=True)
        df['creatinine_max'] = df[results_cols].max(axis=1)
        df['creatinine_min'] = df[results_cols].min(axis=1)
        df["creatinine_max_delta"] = df[results_cols].diff(axis=1).max(axis=1).fillna(0) # note: this is better than df['creatinine_max'] - df['creatinine_min']
        df['creatinine_std'] = df[results_cols].std(axis=1)
        df['most_recent'] = df[results_cols].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
        df['rv1_ratio'] = df['most_recent'] / df['creatinine_min']
        df['rv2_ratio'] = df['most_recent'] / df['creatinine_median']
        df.drop(columns="")
        return df

    def preprocess(self, df):
        df['sex'] = self.le.fit_transform(df['sex'])
        x = self.process_features(df)
        return x
    
    def predict_aki(self, measurement_vector):
        x = self.preprocess(measurement_vector)
        y = self.aki_model.predict(x)
        return y
        
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
    df = df.drop(columns="aki")

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
    print(f"1s: {sum(predictions)}, length:{len(predictions)}")

    # Compute F3 Score
    f3_score_test = fbeta_score(aki_data, predictions, beta=3, zero_division=1)

    print('Final F3 score:', f3_score_test)

