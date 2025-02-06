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
    model = Model("history.csv")
    controller = Controller(model)
    controller.hl7_listen()


if __name__ == "__main__":
    # read the environment variables for the mllp and pager ports
    mllp_port = os.getenv("MLLP_ADDRESS", "localhost:8440")
    pager_port = os.getenv("PAGER_ADDRESS", "localhost:8441")

    # i think passing ports as flags is more work so i used the above for now
    #parser = argparse.ArgumentParser()
    #parser.add_argument("--messages", default="messages.mllp", help="HL7 messages to replay, in MLLP format")
    #parser.add_argument("--mllp", default=8440, type=int, help="Port on which to replay HL7 messages via MLLP")
    #parser.add_argument("--pager", default=8441, type=int, help="Post on which to listen for pager requests via HTTP")
    #flags = parser.parse_args()
    #mllp_port = flags.mllp
    #pager_port = flags.pager

    # run system
    main()
   
    # TODO: In future add preventative measures for system crashes, not relevant for this week however.

