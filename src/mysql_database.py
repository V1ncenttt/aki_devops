from database import Database
from sqlalchemy import create_engine

DATABASE_URI= None #TODO: Add database URI

class MySQLDatabase(Database):
    def __init__(self, host, port, user, password, db):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.engine =  create_engine(DATABASE_URI)
        self.db = db

    def connect(self):
        print(f'Connecting to MySQL database {self.db} at {self.host}:{self.port} as {self.user}')
        # Connect to MySQL database
        pass

    def disconnect(self):
        print(f'Disconnecting from MySQL database {self.db}')
        # Disconnect from MySQL database
        pass

    def execute(self, query):
        print(f'Executing query: {query}')
        # Execute query
        pass

    def add_patient(self, mrn: int, age: int = None) -> None:
        print(f'Adding patient with MRN {mrn} and age {age} to MySQL database {self.db}')
        # Add patient to MySQL database
        pass

    def add_measurement(self, mrn, measurement, test_date) -> None:
        print(f'Adding measurement for patient with MRN {mrn} to MySQL database {self.db}')
        # Add measurement to MySQL database
        pass

    def get_data(self, mrn) -> None:
        print(f'Retrieving data for patient with MRN {mrn} from MySQL database {self.db}')
        # Get data from MySQL database
        pass