<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="img/aki.png" alt="Project logo"></a>
</p>

<h3 align="center">AKI Alerting System</h3>

<div align="center">

[![pipeline status](https://gitlab.doc.ic.ac.uk/vl724/swemls_europe/badges/main/pipeline.svg)](https://gitlab.doc.ic.ac.uk/vl724/swemls_europe/-/pipelines)

[![GitLab Issues](https://img.shields.io/gitlab/issues/vl724/swemls_europe)](https://gitlab.doc.ic.ac.uk/vl724/swemls_europe/-/issues)

[![GitLab Merge Requests](https://img.shields.io/gitlab/merge-requests/vl724/swemls_europe)](https://gitlab.doc.ic.ac.uk/vl724/swemls_europe/-/merge_requests)

[![GitLab license](https://img.shields.io/gitlab/license/vl724/swemls_europe)](https://gitlab.doc.ic.ac.uk/vl724/swemls_europe/-/blob/main/LICENSE)

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