"""
Database Module
===============
This module provides an abstract base class (`Database`) that defines the interface for interacting with a database.

Authors:
--------
- Vincent Lefeuve (vincent.lefeuve.24@imperial.ac.uk)

Classes:
--------
- `Database`: Abstract base class defining methods for retrieving and storing patient data.

Usage:
------
To implement a concrete database, subclass `Database` and provide implementations for all abstract methods.

Example:
--------

class SQLDatabase(Database):
    def get_data(self, mrn: int) -> list[tuple]:
        # Implementation for fetching data
        pass

    def add_measurement(self, mrn: int, measurement: float, test_date: str) -> None:
        # Implementation for adding a new measurement
        pass

    def add_patient(self, mrn: int, age: int = None, sex: str = None) -> None:
        # Implementation for adding a new patient
        pass
        
"""

from abc import ABC, abstractmethod


class Database(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_data(self, mrn):
        """_summary_
        Pulls data from the database for a given patient MRN.

        Args:
            mrn (int): A patients MRN number

        Raises:
            NotImplementedError: This is an abstract method,
            and should be implemented by a subclass
        """

        raise NotImplementedError

    @abstractmethod
    def add_measurement(self, mrn, measurement, test_date) -> None:
        """Adds a creatinine measurement for a patient to the database.

        Args:
            mrn (): A patients MRN number
            measurement (): The creatinine measurement value
            test_date (): The date of the test

        Raises:
            NotImplementedError: This is an abstract method,
            and should be implemented by a subclass
        """
        raise NotImplementedError

    @abstractmethod
    def add_patient(self, mrn, age=None, sex=None) -> None:
        """Adds a new patient to the database.

        Args:
            mrn (): A patients MRN number
            age (): The age of the patient
            sex (): The sex of the patient

        Raises:
            NotImplementedError: This is an abstract method,
            and should be implemented by a subclass
        """
        raise NotImplementedError
    
    #TODO: Can we delete this file?
