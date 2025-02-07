#!/usr/bin/env python3

import argparse
import csv
import os
import sys
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from joblib import dump, load
from sklearn.metrics import accuracy_score, fbeta_score

def add_padding(df):
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

def process_dates(df):
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

def process_features(df):
    """
    Process features of input data for detection of aki. First the dates are turned into seconds (int) and then padding is added to ensure constant length
    of input data. Finally some extra aggregated feature values are computed.

    Args:
        df (Dataframe): Dataframe with input data

    Returns:
        Dataframe : Dataframe with processed features
    """
    results_cols = [col for col in df.columns if "creatinine_result" in col]

    df = process_dates(df)
    df = add_padding(df)

    df['creatinine_mean'] = df[results_cols].mean(axis=1)
    df['creatinine_median'] = df[results_cols].median(axis=1, skipna=True)
    df['creatinine_max'] = df[results_cols].max(axis=1)
    df['creatinine_min'] = df[results_cols].min(axis=1)
    df["creatinine_max_delta"] = df[results_cols].diff(axis=1).max(axis=1).fillna(0) # note: this is better than df['creatinine_max'] - df['creatinine_min']
    df['creatinine_std'] = df[results_cols].std(axis=1)
    df['most_recent'] = df[results_cols].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
    df['rv1_ratio'] = df['most_recent'] / df['creatinine_min']
    df['rv2_ratio'] = df['most_recent'] / df['creatinine_median']

    return df

def preprocess(df, train):
    """
    Preprocess data for training or evaluation.

    Args:
        df (Dataframe) : Dataframe containing data for training or evaluation
        train (bool) : Flag for whether the data is being processed for training (contains aki column) or evaluation (no aki column)
    Returns:
        Dataframe : A Dataframe containing all preprocessed data ready for training or evaluation
    """
    le = LabelEncoder()
    df['sex'] = le.fit_transform(df['sex'])
    if train:
        x_train = process_features(df.drop(columns='aki'))
        df['aki'] = le.fit_transform(df['aki'])
        y_train = df['aki']
        return x_train, y_train
    else:
        x_train = process_features(df)
        return x_train

def train(flags):
    """
    Train an XGBClassifier model on training data for the prediction of aki. First the data is preprocessed for training and then the training is done.

    Args:
        flags : flags of program for reading paths, etc...
    Returns:
        XGBClassifier model : An XGBClassifier model that has been fitted to the data passed with --train
    """
    try:
        train_df = pd.read_csv(flags.train) 
    except Exception as e:
        print(f"Unexpected error when attempting to read {flags.train}:")
        print(e)
        sys.exit(1)

    x_train, y_train = preprocess(train_df, train=True)

    model = XGBClassifier(eval_metric='logloss', scale_pos_weight=100, max_depth=5, learning_rate=0.05, n_estimators=100)
    model.fit(x_train, y_train)

    return model


def eval(flags):
    """
    Compare predictions passed by --eval with ground truths passed by --input. 
    Calculate Accuracy and F3 Score and then print both to stdout.
    
    Args:
        flags : flags passed to model.py from shell
    Returns:
        None : This function does not return anything
    """
    y_pred = pd.read_csv(flags.eval)
    y_test = pd.read_csv(flags.input)

    le = LabelEncoder()
    y_pred = le.fit_transform(y_pred.values.ravel())
    y_test = le.fit_transform(y_test['aki'])

    accuracy = accuracy_score(y_test, y_pred)
    f3 = fbeta_score(y_test, y_pred, beta=3) # 3 seems close to what the tests use
    print(f"ACCURACY: {accuracy} || F3: {f3}")

    return    

def predict(flags, model):
    """
    Run inference on data passed by --input with the chosen model

    Args:
        flags : Flags from program
        model : Chosen model to use for running inference
    Returns:
        ndarray : ndarray containing predictions
    """
    eval_df = pd.read_csv(flags.input)
    x_test = preprocess(eval_df, train=False)
    y_pred = model.predict(x_test)
    return y_pred

def main():
    """
    This program trains and evaluates a machine learning model for Acute Kidney Injury (aki) predictions given data in the format of:
    age, sex, aki, creatinine_date_0, creatinine_result_0, creatinine_date_1, creatinine_result_1,...
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/test.csv", help="Path to data to run inference on.")
    parser.add_argument("--output", default="data/aki.csv", help="Path to write output data.")
    parser.add_argument("--train", default="", help="Path to training data, if not given, the program only evaluates based on chosen model and data.")
    parser.add_argument("--no-infer", action="store_true", help="Flag for skipping inference. By default the model runs inference.")
    parser.add_argument("--model", default="aki_detection.joblib", help="Path to model for evaluation, used if --train argument is not passed.")
    parser.add_argument("--eval", default="", help="Path to a csv containing predictions of model to compare with data from --input.")
    flags = parser.parse_args()

    if len(flags.train) > 0:
        # train model
        print(f"Training model on {flags.train}...", end='')
        model = train(flags)
        print("Done!")

        print("Saving model... ", end='')
        dump(model, 'aki_detection.joblib')
        print("Done!")
    else:
        # load pretrained model
        print(f"Loading model '{flags.model}'... ", end='')
        try:
            model = load(flags.model)
        except Exception as e:
            print(f"Unexpected error when attempting to load model from '{flags.model}':")
            print(e)
            sys.exit(1)
        print("Done!")

    # run inference on flags.input and write predictions to flags.output
    if not flags.no_infer:
        print(f"Running inference on '{flags.input}'...")
        preds = predict(flags, model)
        f = open(flags.output, 'w')
        writer = csv.writer(f)
        writer.writerow(["aki"])
        for pred in preds:
            result = 'y' if pred == 1 else 'n'
            writer.writerow([result])
        f.close()
    
    # evalute Accuracy and F3 from flags.eval (model predictions) and flags.input (ground truth)
    if len(flags.eval) > 0:
        eval(flags)

    print("PROGRAM TERMINATED!")

if __name__ == "__main__":
    main()