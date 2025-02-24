import unittest
from unittest.mock import MagicMock
import pandas as pd
from src.pandas_database import PandasDatabase
from src.data_operator import DataOperator


class TestDataOperator(unittest.TestCase):
    """Unit tests that all of the classes implementing the Database interface
    should pass.
    """

    def setUp(self):
        """Initialize Database Operator before each test."""
        self.database = MagicMock(spec = PandasDatabase)
        self.msg_queue = []
        self.predict_queue = []
        
        # Initialize DataOperator
        self.operator = DataOperator(self.msg_queue, self.predict_queue, self.database)
        
    def test_process_patient(self):
        """Test processing a patient measurement."""
        
            
        
        self.database.get_past_measurements.return_value = [1.2, 1.5, 1.8]  # Expected past measurements (mocked)
        
        # Process patient 
        self.operator.process_patient(123, 1.4, "20250101123000")
        
        self.database.get_past_measurements.assert_called_once_with(123, 1.4, "20250101123000")
        self.database.add_measurement.assert_called_once_with(123, 1.4, "20250101123000")
        
        self.assertEqual(len(self.predict_queue), 1)
        
    def test_process_adt_message(self):
        """Test processing an ADT message."""
        message = ("ADT^A01", {"mrn": 123, "name": "John Doe", "age": 45, "sex": "M"})
        result = self.operator.process_adt_message(message)
        
        # Assertions
        self.database.add_patient.assert_called_once_with(123, 45, "M")
        self.assertFalse(result)
        
    def test_process_oru_message(self):
        """Test processing an ORU message."""
        
        message = ("ORU^R01",{}, [{"mrn": 123, "test_value": 1.8, "test_time": "20250101123000"}])
        
        # remove test dependency from process_patient
        self.operator.process_patient = MagicMock()
        result = self.operator.process_oru_message(message)
        
        # Assertions
        self.operator.process_patient.assert_called_once_with(123, 1.8, "20250101123000")
        self.assertTrue(result)