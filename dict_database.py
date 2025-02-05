"""
blablabla
"""
import csv
from collections import defaultdict
import asyncio

class DictDatabase:
    """_summary_
    """
    def __init__(self, filename):
        """_summary_

        Args:
            filename (_type_): _description_
        """

        self.dict_database = defaultdict(list)
        self.lock = asyncio.Lock()

        # Read the CSV file efficiently
        with open(filename, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            
            # Extract header row
            _ = next(reader)

            # Process each row
            for row in reader:
                mrn = int(row[0])  # First column is MRN
                
                measurements = []

                # Iterate through pairs of (creatinine_result_X, creatinine_date_X)
                for i in range(1, len(row), 2):
                    date = row[i]
                    result = row[i + 1] if i + 1 < len(row) else None

                    if date and result:  # Ensure values are not empty
                        measurements.append((float(result), date))  # Convert result to float
                
                # Store in dictionary
                self.dict_database[mrn] = [{'age': None, 'sex': None}, measurements]
        

    async def get_data(self, mrn):
        """_summary_

        Args:
            mrn (_type_): _description_

        Returns:
            _type_: _description_
        """
        async with self.lock:
            patient_data =  self.dict_database.get(mrn, []) #Prevents KeyError
            age = patient_data[0]['age']
            sex = patient_data[0]['sex']    

            if age is None:
                age = 30
            if sex is None:
                sex = 0
            
            vector = [age, sex]
            for data in patient_data[1]:
                vector.append(data[0])
                vector.append(data[1])

            return vector

        
    async def add_patient(self, mrn, age=None, sex=None):
        """_summary_

        Args:
            mrn (_type_): _description_
            age (_type_, optional): _description_. Defaults to None.
        """
        async with self.lock:
            if mrn not in self.dict_database:
                self.dict_database[mrn] = [{'age': age, 'sex':sex}, []]
            else:
                self.dict_database[mrn][0]['age'] = age
                self.dict_database[mrn][0]['sex'] = sex

    async def add_data(self, mrn, data):
        """_summary_

        Args:
            mrn (_type_): _description_
            data (_type_): _description_
        """
        async with self.lock:
            self.dict_database[mrn].append(data)



   