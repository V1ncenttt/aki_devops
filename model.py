"""_summary_
"""

import random


class Model:
    """_summary_"""

    def __init__(self, database):
        """_summary_

        Args:
            database (_type_): _description_
        """
        self.database = database
        pass

    def create_tensor_from_measurements(self, measurements):
        """_summary_

        Args:
            measurements (_type_): _description_

        Returns:
            _type_: _description_
        """
        return NotImplementedError

    async def add_measurement(self, mrn, measurement, test_date):
        """_summary_

        Args:
            mrn (_type_): _description_
            measurement (_type_): _description_
            test_date (_type_): _description_
        """
        return self.database.add_data(mrn, (measurement, test_date))
    
    def get_past_measurements(self, mrn):
        """_summary_

        Args:
            mrn (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.database.get_data(mrn)

    async def predict_aki(self, mrn, measurements):
        """_summary_

        Args:
            mrn (_type_): _description_
            measurements (_type_): _description_

        Returns:
            _type_: _description_
        """
        # TODO Change this to real model
        prob = random.random()

        if prob > 0.5:
            return True

        return False
