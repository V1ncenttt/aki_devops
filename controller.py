import asyncio
import os
import requests
import logging
import socket
import datetime
from concurrent.futures import ThreadPoolExecutor  # ✅ Add thread pool
from model import Model
from parser import HL7Parser, START_BLOCK, END_BLOCK

import os

# Set the correct host for the HL7 Simulator
SIMULATOR_HOST = os.getenv("SIMULATOR_HOST", "message-simulator")  # Use actual container name
SIMULATOR_PORT = int(os.getenv("SIMULATOR_PORT", "8440"))  # Ensure it's an int




logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
#TODO: Add docstrings to the Controller class
#TODO: Make sure failures are handled properly, especially don't re-add measurements if the model fails
class Controller:
    """HL7 Listener & Worker Controller"""

    def __init__(self, model):
        self.model = model
        self.pager_url = f"http://{os.getenv('PAGER_HOST', 'message-simulator')}:8441/page"
        self.worker_queue = asyncio.Queue()
        self.parser = HL7Parser()
        self.executor = ThreadPoolExecutor(max_workers=5)



    async def worker_manager(self):
        """Manages worker threads and assigns tasks from the queue."""
        while True:
            mrn, creatinine_value, test_time = await self.worker_queue.get()

            
            asyncio.create_task(self.run_worker(mrn, creatinine_value, test_time))

    async def run_worker(self, mrn, creatinine_value, test_time):
        """Runs a worker in a background thread using ThreadPoolExecutor."""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(self.executor, self.process_patient, mrn, creatinine_value, test_time)
        
        if result:
            await self.send_pager_alert(mrn, test_time)

        await loop.run_in_executor(self.executor, self.model.add_measurement, mrn, creatinine_value, test_time)

    async def process_patient(self, mrn, creatinine_value, test_time):
        """Runs ML model inside a worker asynchronously."""
        logging.info(f"[WORKER] Processing Patient {mrn} at {test_time}...")

        patient_vector = await self.model.get_past_measurements(mrn, creatinine_value, test_time)

        alert_needed = self.model.predict_aki(patient_vector)
        logging.info(f"prediction_made:{alert_needed}")
        return alert_needed

    async def hl7_listen(self):
        """Listen for HL7 messages, process them, and assign workers."""
        logging.info(f"[*] Connecting to HL7 Simulator at {SIMULATOR_HOST}:{SIMULATOR_PORT}...")

        while True:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(10)
                client_socket.connect((SIMULATOR_HOST, SIMULATOR_PORT))
                logging.info("[+] Connected to HL7 Simulator!")

                buffer = b""

                while True:
                    try:
                        data = client_socket.recv(1024)
                        if not data:
                            logging.info("[-] No more data, closing connection.")
                            break

                        buffer += data

                        while START_BLOCK in buffer and END_BLOCK in buffer:
                            start_index = buffer.index(START_BLOCK) + 1
                            end_index = buffer.index(END_BLOCK)
                            hl7_message = buffer[start_index:end_index].decode("utf-8").strip()
                            buffer = buffer[end_index + len(END_BLOCK) :]

                            parsed_message = self.parser.parse(hl7_message)
                            
                            # Add error check 
                            if parsed_message is None or parsed_message[0] is None:
                                logging.error("Received invalid HL7 message or unknown message type.")
                                return  # Prevents further errors

                            if parsed_message[0] == "ORU^R01":
                                mrn = parsed_message[2][0]["mrn"]
                                creatinine_value = parsed_message[2][0]["test_value"]
                                test_time = parsed_message[2][0]["test_time"]


                                logging.info(f"Patient {mrn} has creatinine value {creatinine_value} at {test_time}")
                                await self.worker_queue.put((mrn, creatinine_value, test_time))
                                await asyncio.sleep(0)  # Yield control to event loop


                            #In case of patient admission
                            if parsed_message[0] == "ADT^A01":
                                logging.info(parsed_message)
                                mrn = parsed_message[1]["mrn"]
                                name = parsed_message[1]["name"]
                                age = parsed_message[1]["age"]
                                sex = parsed_message[1]['gender']
                                

                                self.model.add_patient(mrn, age, sex)
                                logging.info(f"Patient {name} with MRN {mrn} added to the database")


                            ack_message = self.parser.generate_hl7_ack(hl7_message)
                            client_socket.sendall(ack_message)
                            logging.info(f"[ACK SENT]")

                    except socket.timeout:
                        logging.warning("[-] Read timeout. Closing connection.")
                        break

                client_socket.close()
                logging.info("[*] Connection closed. Waiting 5s before reconnecting...")
                #TODO: Change exit to retry in the future
                exit(0)
                await asyncio.sleep(1)

            except (ConnectionRefusedError, ConnectionResetError):
                logging.error(f"[-] Could not connect to {SIMULATOR_HOST}:{SIMULATOR_PORT}, retrying in 5s...")
                await asyncio.sleep(1)

    async def send_pager_alert(self, mrn, timestamp):
        """Send a pager alert asynchronously."""
        timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "").replace('T', '').split('.')[0]

        logging.info(f"[*] Sending pager alert for Patient {mrn} at {timestamp}...")

        content = f"{mrn},{timestamp}"

        for _ in range(3):  # Retry 3 times if there is a failure
            try:
                response = requests.post(self.pager_url, data=content, timeout=5)
                response.raise_for_status()
                return
            except requests.RequestException as e:
                logging.warning(f"[ALERT FAILED] Retrying... {e}")
                await asyncio.sleep(0.1)  # Wait before retrying


async def main():
    model = Model("history.csv")
    controller = Controller(model)

    asyncio.create_task(controller.worker_manager())  # ✅ Start worker manager
    await controller.hl7_listen()  # ✅ Run HL7 listener

if __name__ == "__main__":
    asyncio.run(main())
