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
from src.parser import HL7Parser
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
    # initialize in reverse order so everything connects to the next module
    parser = HL7Parser() 
    database = PandasDatabase('data/history.csv')
    pager = Pager(pager_address)
    model = Model()
    data_operator = DataOperator(database, model, pager)
    mllp_listener = MllpListener(mllp_address, parser, data_operator)

    # ---------------------------------------------------- #
    # Running the system (stage)
    # ---------------------------------------------------- #
    try:
        while True:
            mllp_listener.run()

            # TODO
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
   

