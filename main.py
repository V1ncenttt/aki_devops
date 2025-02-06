# file/class imports
from parser import HL7Parser 
from model import Model
from data_operator import DataOperator
from pager_operator import PagerOperator

# library imports
#import argparse
import os

def main(mllp_port, pager_port):
    hl7parser = HL7Parser()
    data_operator = DataOperator()
    model = Model()
    pager_operator = PagerOperator()

    # TODO: create running linear pipeline



if __name__ == "__main__":
    # read the environment variables for the mllp and pager ports
    mllp_port = os.getenv("MLLP_ADDRESS", "8440")
    pager_port = os.getenv("PAGER_ADDRESS", "8441")

    # run system
    try:
        main(mllp_port, pager_port)
    except Exception as e:
        print(f"System Error: {e}")
        # TODO: In future add preventative measures for system crashes, not relevant for this week however.

