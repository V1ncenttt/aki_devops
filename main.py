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

    model = Model("history.csv")
    controller = Controller(model)
    controller.hl7_listen(mllp_address)

    # TODO: use async for better pipeline workload balancing
    msg_queue = []#asyncio.Queue()
    parsed_queue = []#asyncio.Queue()
    patient_data = {}

    mllp_listener = MllpListener(mllp_port, msg_queue)
    hl7parser = HL7Parser(msg_queue, parsed_queue)
    data_operator = DataOperator(parsed_queue)
    # unsure how to continue here
    #pager_operator = PagerOperator()

    # TODO: create running linear pipeline
    await asyncio.gather(
        mllp_listener.start(),
        hl7parser.start(),
        data_operator.start(),
    )


    while True:



if __name__ == "__main__":
    # run system
    main()
   
    # TODO: In future add preventative measures for system crashes, not relevant for this week however.

