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

from model import Model
from pandas_database import PandasDatabase
from mllp_listener import MllpListener
from model import Model
from data_operator import DataOperator
from pager import Pager
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
    database = PandasDatabase('history.csv')
    mllp_listener = MllpListener(mllp_address, msg_queue)
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
   

