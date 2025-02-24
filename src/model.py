"""
AKI Detection Module
=====================
This module provides the `Model` class, which is responsible for detecting acute kidney injury (AKI) 
based on creatinine measurements over time. It preprocesses input patient data, extracts relevant features, 
and applies a trained machine learning model to predict AKI occurrence.

Authors:
--------
- Kerim Birgi (kerim.birgi24@imperial.ac.uk)
- Alison Lupton (alison.lupton24@imperial.ac.uk)

Classes:
--------
- `Model`: Loads a trained model and predicts AKI based on processed patient data.

Usage:
------
Example:
    model = Model(predict_queue)
    df = pd.read_csv("test.csv")
    processed_df = model.preprocess(df)
    prediction = model.predict_aki(processed_df)
    print("AKI Prediction:", prediction)

"""

# Imports
import pandas as pd
from joblib import load
import numpy as np
import logging
from sklearn.preprocessing import LabelEncoder



class Model:
    """
    Model for Acute Kidney Injury (AKI) Detection
    =============================================
    This class processes patient data, extracts features, and applies a trained 
    machine learning model to predict the likelihood of AKI.

    Attributes:
    -----------
    - `predict_queue (list)`: Queue containing patient data for prediction.
    - `aki_model (object)`: Preloaded machine learning model for AKI detection.
    - `le (LabelEncoder)`: Label encoder for categorical features.
    """

    def __init__(self, predict_queue):
        """
        Initializes the Model class with a queue and loads the pretrained AKI detection model.
        
        Args:
            predict_queue (list): List containing patient records for AKI prediction.
        """
        self.predict_queue = predict_queue
        self.aki_model = load('aki_detection.joblib')
        self.le = LabelEncoder()


    def add_padding(self, df):
        """
        Ensures each patient's data has a constant length of 50 measurements by adding padding.
        
        Args:
            df (DataFrame): Patient measurement data.

        Returns:
            DataFrame: Padded DataFrame with consistent feature length.
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
        with pd.option_context("future.no_silent_downcasting", True):
            df = df.fillna(0).infer_objects(copy=False)
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
        date_cols = [col for col in df.columns if "creatinine_date" in col]

        df['creatinine_mean'] = df[results_cols].mean(axis=1)
        df['creatinine_median'] = df[results_cols].median(axis=1, skipna=True)
        df['creatinine_max'] = df[results_cols].max(axis=1)
        df['creatinine_min'] = df[results_cols].min(axis=1)
        with pd.option_context("future.no_silent_downcasting", True):
            df["creatinine_max_delta"] = df[results_cols].diff(axis=1).max(axis=1).fillna(0).infer_objects(copy=False) # note: this is better than df['creatinine_max'] - df['creatinine_min']
        df['creatinine_std'] = df[results_cols].std(axis=1)
        df['most_recent'] = df[results_cols].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
        df['rv1_ratio'] = df['most_recent'] / df['creatinine_min']
        df['rv2_ratio'] = df['most_recent'] / df['creatinine_median']
        df = df.drop(columns=results_cols)
        df = df.drop(columns=date_cols)

        with pd.option_context("future.no_silent_downcasting", True):
            df = df.fillna(0).infer_objects(copy=False) # Prevents FutureWarning
        return df

    def preprocess(self, df):
        """
        Prepares input data by encoding categorical variables and extracting features.
        
        Args:
            df (DataFrame): Raw patient data.
        
        Returns:
            DataFrame: Processed DataFrame ready for prediction.
        """
        df['sex'] = self.le.fit_transform(df['sex'])
        x = self.process_features(df)
        return x
    
    def predict_aki(self, measurement_vector):
        """
        Predicts AKI using the preloaded model.
        
        Args:
            measurement_vector (DataFrame): Processed patient data.
        
        Returns:
            int: 1 if AKI is detected, 0 otherwise.
        """
        x = self.preprocess(measurement_vector)
        y = self.aki_model.predict(x)
        logging.info(f"Prediction: {y}")
        return y
        
    def run(self):
        """
        Executes the prediction process on the next patient in the queue.
        
        Returns:
            tuple: (MRN, test_time) if AKI is detected, otherwise None.
        """
        (mrn, test_time, patient_vector) = self.predict_queue.pop(0) 
        try:
            if self.predict_aki(patient_vector):
                return (mrn, test_time)
            else:
                return None
        except Exception as e: #TODO: Catch the right exception
            print("Error in model.py")
            logging.info(f"Exception: {e}")
            exit()

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

