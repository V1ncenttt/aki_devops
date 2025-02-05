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
                self.dict_database[mrn] = measurements
        

    async def get_data(self, mrn):
        """_summary_

        Args:
            mrn (_type_): _description_

        Returns:
            _type_: _description_
        """
        async with self.lock:
            return self.dict_database.get(mrn, []) #Prevents KeyError

    async def add_data(self, mrn, data):
        """_summary_

        Args:
            mrn (_type_): _description_
            data (_type_): _description_
        """
        async with self.lock:
            self.dict_database[mrn].append(data)



if __name__ == "__main__":
    db = DictDatabase("history.csv")
    print(db.get_data(189386394))
    db.add_data(1893806394, (1.2, "2021-03-01"))
    print(db.get_data(1893806394))
   