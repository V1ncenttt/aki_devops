#!/usr/bin/env python3

import argparse
import csv
import os
import sys
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from joblib import dump
from sklearn.metrics import accuracy_score, fbeta_score, roc_curve, auc
from utils import preprocess



def train(train_dataset, output_path = None):
    """Train an XGBClassifier and log the experiment using MLflow."""
    try:
        train_df = pd.read_csv(train_dataset)
    except Exception as e:
        print(f"Error loading training data: {e}")
        sys.exit(1)

    x_train, y_train = preprocess(train_df, train=True)

    model = XGBClassifier(eval_metric='logloss', scale_pos_weight=100, max_depth=5, learning_rate=0.05, n_estimators=100)
    model.fit(x_train, y_train)

    
    # Save the model as joblib
    if not output_path:
        
        time_identifier = pd.Timestamp.now().strftime("%Y%m%d%H%M%S")
        filename = f'aki_detection{time_identifier}.joblib'
        complete_path = os.path.join('model/model_iterations', filename)
        print(f"Saving model to {complete_path}")
        dump(model, complete_path)
    else:
        print(f"Saving model to {output_path}")
        dump(model, output_path)
    
    return model


def predict(flags, model):
    """Run inference using the trained model."""
    eval_df = pd.read_csv(flags.input)
    x_test = preprocess(eval_df, train=False)
    y_pred = model.predict(x_test)
    return y_pred


def main():
    """Main function to handle training, evaluation, and inference."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/training.csv", help="Training data path.")
    parser.add_argument("--no-infer", action="store_true", help="Skip inference.")
    parser.add_argument("--output", help="Model path.")
    flags = parser.parse_args()

    if len(flags.train) > 0:
        print(f"Training model on {flags.train}...", end='')
        model = train(flags.train, flags.output)
        print("Done!")
    
    if not flags.no_infer:
        print(f"Running inference on '{flags.input}'...")
        preds = predict(flags, model)
        with open(flags.output, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["aki"])
            for pred in preds:
                writer.writerow(['y' if pred == 1 else 'n'])

    print("PROGRAM TERMINATED!")


if __name__ == "__main__":
    main()
    #TODO: train with optuna
