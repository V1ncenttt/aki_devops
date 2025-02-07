<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="img/aki.png" alt="Project logo"></a>
</p>

<h3 align="center">AKI Alerting System</h3>

<div align="center">

</div>

---

<p align="center"> 
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>

This project focuses on deploying an Acute Kidney Injury (AKI) detection system using real-time HL7 messages. The system is designed to run in a single Docker container and operates in a simulated hospital environment before real-world deployment.

The system processes historical and live blood test data, detects potential AKI cases based on creatinine levels, and triggers pager alerts for medical intervention. It integrates with an HL7 simulator via the MLLP protocol and acknowledges messages to maintain a reliable data stream

## Repository Structure <a name = "Repository Structure"></a>
Our repository follows a modular structure, ensuring clear separation of core application logic, model training, testing, and simulation. This improves maintainability, scalability, and deployment efficiency.
```
├── data/                  # Training data and historical patient records
├── img/                   # Images and visualizations (e.g., for documentation)
├── model/                 # Model training scripts and related files
├── simulation/            # HL7 simulator and related files
├── src/                   # Core application logic
│   ├── __init__.py        # Module initialization
│   ├── data_operator.py   # Manages data processing and database updates
│   ├── database.py        # Database handling
│   ├── mllp_listener.py   # Listens for HL7 messages over MLLP
│   ├── model.py           # Predicts AKI from patient data
│   ├── pager.py           # Sends alerts if AKI is detected
│   ├── pandas_database.py # Manages patient data with Pandas
│   ├── parser.py          # Parses HL7 messages
├── test/                  # Unit tests for various system components
├── .gitignore             # Specifies files and folders to be ignored by Git
├── Dockerfile             # Docker configuration for the main system
├── README.md              # Project documentation
├── aki_detection.joblib   # Pretrained AKI detection model
├── compose.yaml           # Docker Compose configuration
├── main.py                # Entry point for running the system
├── makefile               # Makefile for automating tasks
├── requirements.txt       # Python dependencies
├── run_tests.py           # Test runner for unit tests
```
1. src/ – Core Application
The main logic of the system is contained within the src/ folder. It includes:

mllp_listener.py → Listens for HL7 messages from the hospital system.
parser.py → Parses incoming HL7 messages.
data_operator.py → Handles database updates and data flow.
database.py / pandas_database.py → Stores and retrieves patient records.
model.py → Loads the trained AKI detection model and makes predictions.
pager.py → Sends alerts if an AKI case is detected.

2. model/ – Model Training
Contains scripts used for training the AKI detection model. The trained model is stored as:

aki_detection.joblib → The saved ML model used for inference.

3. data/ – Training & Historical Data
This directory contains:

Historical blood test records used to initialize the database.

4. simulation/ – HL7 Simulator
Contains all simulator-related files, ensuring better separation of concerns:

HL7 message replay system
MLLP simulator
Docker Compose setup for multi-container testing

5. test/ – Unit Tests
Contains unit and integration tests to validate the system:

6. img/ – Documentation Assets
Contains images and visualizations for README and documentation.

7. Root-Level Files
main.py → The entry point of the system.
Dockerfile → Docker configuration for deployment.
compose.yaml → Defines multi-container setup for the system.
requirements.txt → List of Python dependencies.
run_tests.py → Runs all unit tests.

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

All of the prerequisites are automatically installed so you don't have to think about it.

### Installing

To install, simply clone the repository and use the dockerfile/ compose.

## 🔧 Running the tests <a name = "tests"></a>

In order to test  the system, you can simply run:

```shell
make unittest
```

This will trigger all the unit tests.
If you want to add a coverage report, then run:

```shell
make unittest_coverage
```

## ⛏️ Model Training <a name = "model_training"></a>

If you want to train and evaluate the model, run:

```shell
make eval
```

If you want to log the model in mlflow, run:

```shell
make mlflow
```

## 🎈 Usage <a name="usage"></a>

The system in itself is meant to be used in a docker container, either alone using the dockerfile, or if you want to also use the simulator, you can run:

```shell
docker-compose up --build
```
Which will run both the system and the message simulator, as well as installing all of the dependencies.

## 🚀 Deployment <a name = "deployment"></a>

Deployment using kubernetes has not yet been done.

## ⛏️ Built Using <a name = "built_using"></a>

- [XgBoost](https://xgboost.readthedocs.io/en/stable/) - ML Model
- [MlFlow](https://mlflow.org/) - Model monitoring

## ✍️ Authors <a name = "authors"></a>

- [Kerim Birgi](mailto:kerim.birgi24@imperial.ac.uk) - Group Member
- [Zala Breznik](mailto:zala.breznik24@imperial.ac.uk) - Group Member
- [Lorenz Heiler](mailto:lorenz.heiler24@imperial.ac.uk) - Group Member
- [Vincent Lefeuve](mailto:vincent.lefeuve24@imperial.ac.uk) - Group Member
- [Alison Lupton](mailto:alison.lupton24@imperial.ac.uk) - Group Member