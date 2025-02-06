# file/class imports
from parser import HL7Parser 
from model import Model
from controller import Controller 
from pandas_database import PandasDatabase

from mllp_listener import MllpListener
from parser import HL7Parser 
from model import Model
from data_operator import DataOperator


# library imports
#import argparse
import os
import asyncio

def main():
    # read the environment variables for the mllp and pager ports
    mllp_address = os.getenv("MLLP_ADDRESS", "message-simulator:8440")
    pager_address = os.getenv("PAGER_ADDRESS", "message-simulator:8441")

    # TODO: use async for better pipeline workload balancing

    # ---------------------------------------------------- #
    # initialization stage
    # ---------------------------------------------------- #
    msg_queue = []#asyncio.Queue()
    parsed_queue = []#asyncio.Queue()
    predict_queue = []
    patient_data = {}

    mllp_listener = MllpListener(mllp_address, msg_queue)
    #hl7parser = HL7Parser(msg_queue, parsed_queue)
    data_operator = DataOperator(msg_queue, predict_queue)
    model = Model("history.csv", predict_queue)

    # ---------------------------------------------------- #
    # Running the system (stage)
    # ---------------------------------------------------- #
    try:
        while True:
            mllp_listener.run()
            data_operator.run()
    except Exception as e:
        print(f"Exception occured:\n{e}")
        print("Process interrupted")


    # ---------------------------------------------------- #
    #shutdown stage
    # ---------------------------------------------------- #
    mllp_listener.shutdown()  
    




if __name__ == "__main__":
    # run system
    main()
   
    # TODO: In future add preventative measures for system crashes, not relevant for this week however.

