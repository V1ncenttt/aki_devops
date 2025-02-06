# file/class imports
from parser import HL7Parser 
from model import Model
from controller import Controller 
from pandas_database import PandasDatabase

# library imports
#import argparse
import os
import asyncio

def main():
    # read the environment variables for the mllp and pager ports
    mllp_address = os.getenv("MLLP_ADDRESS", "message-simulator:8440")
    pager_address = os.getenv("PAGER_ADDRESS", "message-simulator:8441")

    model = Model("history.csv")
    controller = Controller(model, pager_address)
    controller.hl7_listen(mllp_address)


if __name__ == "__main__":
    # run system
    main()
   
    # TODO: In future add preventative measures for system crashes, not relevant for this week however.

