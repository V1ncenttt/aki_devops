<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="img/aki.png" alt="Project logo"></a>
</p>

<h3 align="center">AKI Alerting System</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![GitHub Issues](https://img.shields.io/github/issues/kylelobo/The-Documentation-Compendium.svg)](https://github.com/kylelobo/The-Documentation-Compendium/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/kylelobo/The-Documentation-Compendium.svg)](https://github.com/kylelobo/The-Documentation-Compendium/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

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
- [Built Using](#built_using)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>

This project focuses on deploying an Acute Kidney Injury (AKI) detection system using real-time HL7 messages. The system is designed to run in a single Docker container and operates in a simulated hospital environment before real-world deployment.

The system processes historical and live blood test data, detects potential AKI cases based on creatinine levels, and triggers pager alerts for medical intervention. It integrates with an HL7 simulator via the MLLP protocol and acknowledges messages to maintain a reliable data stream

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them.

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running.

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo.

## 🔧 Running the tests <a name = "tests"></a>

In order to test  the system, you can simply run:

```shell
python3 run_tests.py
```

This will trigger all the unit tests.
If you want to add a coverage report, then run:

```shell
python3 run_tests.py --coverage
```

Which will create an HTML coverage report in /coverage_html_report/index.html

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## 🎈 Usage <a name="usage"></a>

Add notes about how to use the system.

## 🚀 Deployment <a name = "deployment"></a>

Add additional notes about how to deploy this on a live system.

## ⛏️ Built Using <a name = "built_using"></a>

- [MongoDB](https://www.mongodb.com/) - Database
- [Express](https://expressjs.com/) - Server Framework
- [VueJs](https://vuejs.org/) - Web Framework
- [NodeJs](https://nodejs.org/en/) - Server Environment

## ✍️ Authors <a name = "authors"></a>

- [Kerim Birgi](mailto:kerim.birgi24@imperial.ac.uk) - Group Member
- [Zala Breznik](mailto:zala.breznik24@imperial.ac.uk) - Group Member
- [Lorenz Heiler](mailto:lorenz.heiler24@imperial.ac.uk) - Group Member
- [Vincent Lefeuve](mailto:vincent.lefeuve24@imperial.ac.uk) - Group Member
- [Alison Lupton](mailto:alison.lupton24@imperial.ac.uk) - Group Member