# file/class imports
from mllp_listener import MllpListener
from parser import HL7Parser 
from model import Model
from data_operator import DataOperator
from pager_operator import PagerOperator

# library imports
import asyncio
import os

async def main(mllp_port, pager_port):

    msg_queue = asyncio.Queue()
    parsed_queue = asyncio.Queue()
    patient_data = {}

    mllp_listener = MllpListener(mllp_port, msg_queue)
    hl7parser = HL7Parser(msg_queue, parsed_queue)
    data_operator = DataOperator(parsed_queue)
    # unsure how to continue here
    pager_operator = PagerOperator()

    # TODO: create running linear pipeline
    await asyncio.gather(
        mllp_listener.start(),
        hl7parser.start(),
        data_operator.start(),
    )




if __name__ == "__main__":
    # read the environment variables for the mllp and pager ports
    mllp_port = os.getenv("MLLP_ADDRESS", "localhost:8440")
    pager_port = os.getenv("PAGER_ADDRESS", "localhost:8441")

    # run system
    try:
        main(mllp_port, pager_port)
    except Exception as e:
        print(f"System Error: {e}")
        # TODO: In future add preventative measures for system crashes, not relevant for this week however.

