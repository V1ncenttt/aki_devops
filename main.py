# file/class imports
from parser import HL7Parser 
from model import Model
from controller import Controller 

# library imports
#import argparse
import os
import asyncio

async def main(mllp_port, pager_port):
    #hl7parser = HL7Parser() currently not needed as controller initializes on its own, refactor in future ideally
    model = Model("history.csv")
    controller = Controller(model)

    asyncio.create_task(controller.worker_manager())
    await controller.hl7_listen()



if __name__ == "__main__":
    # read the environment variables for the mllp and pager ports
    mllp_port = os.getenv("MLLP_ADRESS", "8440")
    pager_port = os.getenv("PAGER_ADRESS", "8441")

    # i think passing ports as flags is more work so i used the above for now
    #parser = argparse.ArgumentParser()
    #parser.add_argument("--messages", default="messages.mllp", help="HL7 messages to replay, in MLLP format")
    #parser.add_argument("--mllp", default=8440, type=int, help="Port on which to replay HL7 messages via MLLP")
    #parser.add_argument("--pager", default=8441, type=int, help="Post on which to listen for pager requests via HTTP")
    #flags = parser.parse_args()
    #mllp_port = flags.mllp
    #pager_port = flags.pager

    # run system
    try:
        asyncio.run(main(mllp_port, pager_port))
    except Exception as e:
        print(f"System Error: {e}")
        # TODO: In future add preventative measures for system crashes, not relevant for this week however.

