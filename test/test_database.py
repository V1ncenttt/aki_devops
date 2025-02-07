import unittest
from pandas_database import PandasDatabase

class TestDatabase(unittest.TestCase):
    """Unit tests that all of the classes implementing the Database interface
    should pass.
    """
    def setUp(self):
        """Initialize Database before each test."""
        self.db = PandasDatabase('history.csv')
    
    #TODO: Maybe there's a pb with how dates are handled when stored in the db?????
    def test_get_data(self):
        """Test getting patient data from the database."""

        patient_row = self.db.get_data(189386394)
        self.assertEqual(patient_row['age'].to_numpy(), None)
        self.assertEqual(patient_row['sex'].to_numpy(), None)
        self.assertEqual(patient_row['creatinine_result_0'].to_numpy(), 126.48)
        self.assertEqual(self.datetime_array_to_str(patient_row['creatinine_date_4'].to_numpy()), '20240206144500')
                         
    def test_add_patient_new(self):
        """Test adding a patient to the database."""
        self.db.add_patient(123, 30, 'M')
        patient_row = self.db.get_data(123)
        self.assertEqual(patient_row['age'].to_numpy(), 30)
        self.assertEqual(patient_row['sex'].to_numpy(), 'M')
    
    def test_add_patient_existing(self):
        """Test updating a patient's information in the database."""
        before = self.db.get_data(189386394)
        self.db.add_patient(189386394, 31, 'F')
        patient_row = self.db.get_data(189386394)
        self.assertEqual(patient_row['age'].to_numpy(), 31)
        self.assertEqual(patient_row['sex'].to_numpy(), 'F')
        

        measurements_before = before.drop(columns=['age','sex'])
        measurements_after = patient_row.drop(columns=['age','sex'])

        self.assertEqual(measurements_before.shape, measurements_after.shape)
        self.assertTrue(measurements_before.equals(measurements_after))


    def datetime_array_to_str(self, datetime_array):
        date = datetime_array[0]
        return str(date).replace('-', '').replace(':', '').replace(' ', '').replace('T', '').split('.')[0]

    def test_add_measurement(self):
        """Test adding a measurement to the database."""
        self.db.add_patient(25, 30, 'M') #First add dummy patient

        self.db.add_measurement(25, 1.2, '20230101120000')
        patient_row = self.db.get_data(25)

        self.assertEqual(patient_row['creatinine_result_0'].to_numpy(), 1.2)
        self.assertEqual(self.datetime_array_to_str(patient_row['creatinine_date_0'].to_numpy()), '20230101120000')

        self.db.add_measurement(25, 1.5, '20230101120005')
        patient_row = self.db.get_data(25)

        self.assertEqual(patient_row['creatinine_result_1'].to_numpy(), 1.5)
        self.assertEqual(self.datetime_array_to_str(patient_row['creatinine_date_1'].to_numpy()), '20230101120005')



    
        
