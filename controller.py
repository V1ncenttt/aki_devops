"""_summary_
"""

import asyncio
import requests
import logging
import socket
import datetime
from model import Model
from parser import HL7Parser


SIMULATOR_HOST = "127.0.0.1"
SIMULATOR_PORT = 8440
# MLLP Delimiters
START_BLOCK = b"\x0b"  # VT (Vertical Tab)
END_BLOCK = b"\x1c\r"  # FS (File Separator) + Carriage Return

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
class Controller:
    """_summary_"""

    def __init__(self, model):
        """_summary_"""
        self.model = model
        self.pager_url = "http://localhost:8441/page"
        self.worker_queue = asyncio.Queue()
        self.parser = HL7Parser()

    @staticmethod
    def generate_hl7_ack(message: str) -> bytes:
        """Generate an HL7 ACK message."""
        msg_control_id = "UNKNOWN"
        segments = message.split("\r")

        for segment in segments:
            if segment.startswith("MSH"):
                parts = segment.split("|")
                if len(parts) > 9:
                    msg_control_id = parts[9]

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        hl7_ack = f"MSH|^~\\&|||||{timestamp}||ACK^R01|{msg_control_id}|2.5\rMSA|AA|{msg_control_id}\r"

        return START_BLOCK + hl7_ack.encode("utf-8") + END_BLOCK

    async def worker(self, worker_id):
        while True:
            mrn, creatinine_value, test_time = await self.worker_queue.get()

            try:
                if creatinine_value is None:
                    logging.warning(
                        f"[WORKER {worker_id}] No creatinine value for Patient {mrn}. Skipping."
                    )
                    continue

                alert_needed = await self.model.predict_aki(mrn, creatinine_value)

                if alert_needed:
                    await self.send_pager_alert(mrn, test_time)

            except Exception as e:
                logging.error(
                    f"[WORKER {worker_id}] Failed processing Patient {mrn}: {e}"
                )

            self.worker_queue.task_done()

    async def hl7_listen(self):
        """Listen for HL7 messages, process them, and assign workers."""
        logging.info(
            f"[*] Connecting to HL7 Simulator at {SIMULATOR_HOST}:{SIMULATOR_PORT}..."
        )

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
                            hl7_message = (
                                buffer[start_index:end_index].decode("utf-8").strip()
                            )
                            buffer = buffer[end_index + len(END_BLOCK) :]

                            

                            parsed_message = self.parser.parse(hl7_message)
                            if parsed_message[0] == "ORU^R01":

                                mrn = parsed_message[2][0]["mrn"]
                                creatinine_value = parsed_message[2][0]["test_value"]
                                test_time = parsed_message[2][0]["test_time"]

                                logging.info(f"Patient {mrn} has creatinine value {creatinine_value} at {test_time}")
                                await self.worker_queue.put(
                                    (mrn, creatinine_value, test_time)
                                )
                                await asyncio.sleep(0)  # Yield control to event loop

                            ack_message = self.generate_hl7_ack(hl7_message)
                            client_socket.sendall(ack_message)
                            logging.info(f"[ACK SENT]")

                    except socket.timeout:
                        logging.warning("[-] Read timeout. Closing connection.")
                        break

                client_socket.close()
                logging.info("[*] Connection closed. Waiting 5s before reconnecting...")
                await asyncio.sleep(1)

            except (ConnectionRefusedError, ConnectionResetError):
                logging.error(
                    f"[-] Could not connect to {SIMULATOR_HOST}:{SIMULATOR_PORT}, retrying in 5s..."
                )
                await asyncio.sleep(1)

    async def supervise(self):
        """Monitors workers and restarts them if they fail."""

        worker_tasks = {asyncio.create_task(self.worker(i)): i for i in range(5)}

        while True:
            done, _ = await asyncio.wait(
                worker_tasks.keys(), return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                worker_id = worker_tasks[task]
                worker_tasks.pop(task)
                worker_tasks[asyncio.create_task(self.worker(worker_id))] = worker_id

    async def send_pager_alert(self, mrn, timestamp):
        """_summary_

        Args:
            mrn (_type_): _description_
            timestamp (_type_): _description_
        """
        # Convert timestamp to string with just numbers: '2024-01-20 22:34' becomes 202401202243 (YYYYMMDDHHMMSS)
        timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "").replace('T', '').split('.')[0]

        logging.info(f"[*] Sending pager alert for Patient {mrn} at {timestamp}...")

        content = f"{mrn},{timestamp}"

        for _ in range(3):  # Retry 3 times if there is a failure
            try:
                response = requests.post(self.pager_url, data=content, timeout=5)
                response.raise_for_status()
                return

            except requests.RequestException as e:
                await asyncio.sleep(0.1)  # Wait before retrying


# Main function of the system
async def main():
    model = Model("history.csv")

    controller = Controller(model)

    asyncio.create_task(controller.supervise())
    await controller.hl7_listen()


if __name__ == "__main__":
    asyncio.run(main())
