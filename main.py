"""
Main System Module
==================
This module initializes and runs the HL7 message processing system, handling message reception, parsing,
prediction, and alerting mechanisms.

Usage:
------
Run this script to start the system:
    python main.py

"""

# file/class imports

from src.pandas_database import PandasDatabase
from src.mllp_listener import MllpListener
from src.model import Model
from src.data_operator import DataOperator
from src.pager import Pager
from src.mysql_database import MySQLDatabase
import os

def main():
    """
    Main function that initializes and runs the HL7 message processing system.
    """
    # read the environment variables for the mllp and pager ports
    mllp_address = os.getenv("MLLP_ADDRESS", "message-simulator:8440")
    pager_address = os.getenv("PAGER_ADDRESS", "message-simulator:8441")

    # ---------------------------------------------------- #
    # initialization stage
    # ---------------------------------------------------- #
    msg_queue = []#asyncio.Queue()
    parsed_queue = []#asyncio.Queue()
    predict_queue = []
    patient_data = {}
    database = MySQLDatabase()
    mllp_listener = MllpListener(mllp_address, msg_queue)
    #TODO: Does the database get automatically filled when initialised? 
    data_operator = DataOperator(msg_queue, predict_queue, database)
    model = Model(predict_queue)
    pager = Pager(pager_address)

    # ---------------------------------------------------- #
    # Running the system (stage)
    # ---------------------------------------------------- #
    try:
        while True:
            mllp_listener.run()
            keep_running = data_operator.run()
            if keep_running:
                page_team = model.run()
                if not (page_team == None):
                    pager.run(*page_team)

            
    except Exception as e:
        print(f"Exception occured:\n{e}")
        print("Process interrupted")


    # ---------------------------------------------------- #
    #shutdown stage
    # ---------------------------------------------------- #
    mllp_listener.shutdown()  
    




if __name__ == "__main__":
    """
    Entry point for running the system.
    """
    main()
   

