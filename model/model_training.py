#!/usr/bin/env python3

import argparse
import csv
import os
import sys
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from joblib import dump, load
from sklearn.metrics import accuracy_score, fbeta_score

def add_padding(df):
    """Ensures the dataframe has a constant length of 50."""
    for i in range(((len(df.columns) - 2) // 2), 50):
        df[f'creatinine_date_{i}'] = 0
        df[f'creatinine_result_{i}'] = 0
    return df

def process_dates(df):
    """Converts timestamps to seconds relative to the first measurement."""
    date_cols = [col for col in df.columns if "creatinine_date" in col]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df['ref_date'] = df[date_cols].min(axis=1)
    for col in date_cols:
        df[col] = (df[col] - df['ref_date']).dt.total_seconds()
    df = df.drop(columns=['ref_date']).fillna(0)
    return df

def process_features(df):
    """Feature engineering for AKI prediction."""
    results_cols = [col for col in df.columns if "creatinine_result" in col]

    df = process_dates(df)
    df = add_padding(df)

    df['creatinine_mean'] = df[results_cols].mean(axis=1)
    df['creatinine_median'] = df[results_cols].median(axis=1, skipna=True)
    df['creatinine_max'] = df[results_cols].max(axis=1)
    df['creatinine_min'] = df[results_cols].min(axis=1)
    df["creatinine_max_delta"] = df[results_cols].diff(axis=1).max(axis=1).fillna(0)
    df['creatinine_std'] = df[results_cols].std(axis=1)
    df['most_recent'] = df[results_cols].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
    df['rv1_ratio'] = df['most_recent'] / df['creatinine_min']
    df['rv2_ratio'] = df['most_recent'] / df['creatinine_median']

    return df

def preprocess(df, train):
    """Prepares data for model training or inference."""
    le = LabelEncoder()
    df['sex'] = le.fit_transform(df['sex'])
    if train:
        x_train = process_features(df.drop(columns='aki'))
        df['aki'] = le.fit_transform(df['aki'])
        y_train = df['aki']
        return x_train, y_train
    else:
        return process_features(df)

def train(flags):
    """Train an XGBClassifier and log the experiment using MLflow."""
    try:
        train_df = pd.read_csv(flags.train)
    except Exception as e:
        print(f"Error loading training data: {e}")
        sys.exit(1)

    x_train, y_train = preprocess(train_df, train=True)

    model = XGBClassifier(eval_metric='logloss', scale_pos_weight=100, max_depth=5, learning_rate=0.05, n_estimators=100)
    model.fit(x_train, y_train)

    if flags.mlflow:
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params({
                "eval_metric": "logloss",
                "scale_pos_weight": 100,
                "max_depth": 5,
                "learning_rate": 0.05,
                "n_estimators": 100
            })

            # Log model
            mlflow.sklearn.log_model(model, "aki_model")
            mlflow.log_artifact(flags.train)

            # Save locally
            dump(model, 'aki_detection.joblib')

    return model

def eval(flags):
    """Evaluate predictions and log metrics using MLflow."""
    y_pred = pd.read_csv(flags.eval)
    y_test = pd.read_csv(flags.input)

    le = LabelEncoder()
    y_pred = le.fit_transform(y_pred.values.ravel())
    y_test = le.fit_transform(y_test['aki'])

    accuracy = accuracy_score(y_test, y_pred)
    f3 = fbeta_score(y_test, y_pred, beta=3)

    # Log metrics in MLflow
    if flags.mlflow:
        mlflow.log_metrics({"accuracy": accuracy, "f3_score": f3})

    print(f"ACCURACY: {accuracy} || F3: {f3}")

def predict(flags, model):
    """Run inference using the trained model."""
    eval_df = pd.read_csv(flags.input)
    x_test = preprocess(eval_df, train=False)
    y_pred = model.predict(x_test)
    return y_pred

def main():
    """Main function to handle training, evaluation, and inference."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/test.csv", help="Input data path.")
    parser.add_argument("--output", default="data/aki.csv", help="Output path.")
    parser.add_argument("--train", default="", help="Training data path.")
    parser.add_argument("--no-infer", action="store_true", help="Skip inference.")
    parser.add_argument("--model", default="aki_detection.joblib", help="Model path.")
    parser.add_argument("--eval", default="", help="Evaluation data path.")
    parser.add_argument("--mlflow_uri", default="http://localhost:8000", help="MLflow tracking URI.")
    parser.add_argument("--mlflow", action="store_true", help="Enable MLflow tracking.")
    flags = parser.parse_args()

    if flags.mlflow:
        print("Starting MLflow...")
        
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        token = os.getenv("MLFLOW_TRACKING_TOKEN")

        os.environ["MLFLOW_TRACKING_TOKEN"] = token
        mlflow.set_tracking_uri(tracking_uri)
        
        client = MlflowClient(tracking_uri=tracking_uri)
        experiment_name = "AKI Detection"
        if not client.get_experiment_by_name(experiment_name):
            client.create_experiment(experiment_name)
        mlflow.set_experiment(experiment_name)
        print("MLflow started!")

    if len(flags.train) > 0:
        print(f"Training model on {flags.train}...", end='')
        model = train(flags)
        print("Done!")
    else:
        print(f"Loading model '{flags.model}'... ", end='')
        try:
            model = load(flags.model)
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)
        print("Done!")

    if not flags.no_infer:
        print(f"Running inference on '{flags.input}'...")
        preds = predict(flags, model)
        with open(flags.output, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["aki"])
            for pred in preds:
                writer.writerow(['y' if pred == 1 else 'n'])

    if len(flags.eval) > 0:
        eval(flags)

    print("PROGRAM TERMINATED!")

if __name__ == "__main__":
    main()
