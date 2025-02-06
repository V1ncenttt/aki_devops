from pandas_database import PandasDatabase

class DataOperator:
    def __init__(self):
        self.database = PandasDatabase()
    
    def process_message(message):
        if (message['sender'] == 'PAS'):
            add_patient()
        else:
            add_test()
            
