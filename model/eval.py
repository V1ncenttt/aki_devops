import pandas as pd 
from sklearn.metrics import accuracy_score, fbeta_score, roc_curve, auc
from sklearn.preprocessing import LabelEncoder
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
import os
import sys
import argparse
import matplotlib.pyplot as plt
from joblib import dump, load
from utils import preprocess

def log_roc_curve(X_test, y_test, model, experiment_name="ROC Curve", ):
    """Logs the ROC curve to MLflow."""

    y_pred_prob = model.predict_proba(X_test)[:, 1]

    fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)
    roc_auc = auc(fpr, tpr)

    # Plot ROC curve
    plt.figure()
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")

    # Save plot to file and log to MLflow
    plot_path = f"img/roc_curve_{experiment_name.replace(' ', '_')}.png"
    plt.savefig(plot_path)
    mlflow.log_artifact(plot_path)
    plt.close()

def get_last_model_iteration():
    """Get the last model iteration from the model directory."""
    models = [f for f in os.listdir("model/model_iterations") if f.endswith(".joblib")]
    if not models:
        print("No model iterations found.")
        return None
    return sorted(models)[-1]

def eval(dataset_path, model_path, mlflow_bool):
    """Evaluate predictions and log metrics using MLflow."""
    try:
        dataset = pd.read_csv(dataset_path)

    except Exception as e:
        print(f"Error loading evaluation or input data: {e}")
        sys.exit(1)
    print(dataset.columns)
    y_test = dataset['aki'].map({'y': 1, 'n': 0})
    X_before = dataset.drop(['aki'], axis=1)
    X_test = preprocess(X_before, train=False)

    # Load the model
    model = load(model_path) if model_path else load(f"model/model_iterations/{get_last_model_iteration()}")

    y_pred = model.predict(X_test)
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    f3 = fbeta_score(y_test, y_pred, beta=3)

    print(f"ACCURACY: {accuracy} || F3: {f3}")

    # Log metrics and model to MLflow
    if flags.mlflow:
        with mlflow.start_run() as run:
            # Log metrics
            mlflow.log_metrics({"accuracy": accuracy, "f3_score": f3})

            log_roc_curve(X_test, y_test, model, experiment_name="AKI Detection")
            # Log the model if it exists
            model_file = model_path if model_path else f"model/model_iterations/{get_last_model_iteration()}"
            print(f"Logging model '{model_file}' to MLflow...")
            
            model_name = "Xgboost_AKI_Model"

            # Log the loaded model to MLflow

            mlflow.xgboost.log_model(
                model,
                artifact_path="xgboost_model",
                registered_model_name=model_name
            )

            print(f"Model successfully logged under name: {model_name}")
    else:
        print(f"Error: Model file '{model_file}' not found. Skipping model logging.")

    

def set_mlflow(flags):
    if flags.mlflow:
        print("Starting MLflow...")
        if not flags.onserver:
            mlflow.set_tracking_uri("http://localhost:8000")
            experiment_name = "AKI Detection"
            if not mlflow.get_experiment_by_name(experiment_name):
                mlflow.create_experiment(experiment_name)
            mlflow.set_experiment(experiment_name)
        else:
            tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
            token = os.getenv("MLFLOW_TRACKING_TOKEN")
            os.environ["MLFLOW_TRACKING_TOKEN"] = token
            mlflow.set_tracking_uri(tracking_uri)
            client = MlflowClient(tracking_uri=tracking_uri)
            experiment_name = "AKI Detection"
            if not client.get_experiment_by_name(experiment_name):
                client.create_experiment(experiment_name)
            mlflow.set_experiment(experiment_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/test.csv", help="Evaluation data path.")
    parser.add_argument("--model", default=None, help="Model path.")
    parser.add_argument("--mlflow", action="store_true", help="Log metrics and model to MLflow.")
    parser.add_argument("--mlflow_uri", default="http://localhost:8000", help="MLflow tracking URI.")
    parser.add_argument("--onserver", action="store_true", help="Use local MLflow server.", default=False)

    flags = parser.parse_args()

    set_mlflow(flags)
    eval(flags.input, flags.model, flags.mlflow)