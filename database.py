
from abc import ABC, abstractmethod

class Database(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def get_data(self, mrn):
        raise NotImplementedError
    
    @abstractmethod
    def add_measurement(self, mrn, measurement, test_date):
        raise NotImplementedError
    
    @abstractmethod
    def add_patient(self, mrn, age=None, sex=None):
        raise NotImplementedError
    