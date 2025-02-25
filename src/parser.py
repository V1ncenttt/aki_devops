"""
HL7Parser Module
================
This module provides the `HL7Parser` class,
which is responsible for parsing HL7 messages.
It supports extracting patient data,
blood test results, and generating HL7 acknowledgment messages.
This module is a singleton, ensuring only one instance of the parser is created.

Authors:
--------
- Zala breznik (zala.breznik24@imperial.ac.uk)

Classes:
--------
- `HL7Parser`: Parses HL7 messages and extracts relevant details.

Constants:
----------
- `START_BLOCK (bytes)`: MLLP start delimiter (`\x0b`).
- `END_BLOCK (bytes)`: MLLP end delimiter (`\x1c\r`).

Usage:
------
Example:
    parser = HL7Parser()
    message_type, patient_data, blood_tests = parser.parse(hl7_message)

    if message_type == "ADT^A01":
        print(f"Patient admitted: {patient_data}")

    elif message_type == "ORU^R01":
        print(f"Blood test results: {blood_tests}")

"""

from datetime import datetime
import logging

# MLLP Delimiters
START_BLOCK = b"\x0b"
END_BLOCK = b"\x1c\r"


def singleton(class_):
    """
    Defines singletons as a decorator.
    """
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class HL7Parser:
    """
    HL7Parser Class
    ===============
    This class is responsible for parsing HL7 messages, extracting key data based on message type,
    and generating HL7 acknowledgment messages. This class is a singleton.


    Supported HL7 message types:
    ----------------------------
    - **ADT^A01 (Admission Notification)** → Extracts patient details.
    - **ADT^A03 (Discharge Notification)** → Extracts minimal patient details.
    - **ORU^R01 (Observation Report - Laboratory Results)** → Extracts test results.

    Attributes:
    -----------
    - `message_type (str | None)`: Type of the parsed HL7 message.
    - `test_timestamp (str | None)`: Timestamp of a test in ORU^R01 messages.
    - `patient_data (dict)`: Dictionary storing patient details.
    - `blood_tests (list)`: List of extracted blood test results.

    Methods:
    --------
    - `reset()`: Clears stored data.
    - `calculate_age(dob: str) -> int | None`: Computes patient age from date of birth.
    - `parse(message: str) -> tuple[str | None, dict | None, list | None]`: Parses an HL7 message.
    - `generate_hl7_ack(message: str) -> bytes`: Generates an HL7 acknowledgment (ACK) message.
    """

    def __init__(self) -> None:
        """Initialize the parser with default values."""
        self.message_type = None
        self.test_timestamp = None
        self.init_time = datetime.now().isoformat()
        self.reset()

    def reset(self) -> None:
        """
        Reset the parser's stored data to ensure clean parsing for a new message.
        """
        self.message_type = None
        self.patient_data = {}
        self.blood_tests = []
        self.test_timestamp = None

    def calculate_age(self, dob: str) -> int:
        """
        Calculates a patient's age based on their date of birth (DOB).

        Parameters:
        -----------
        - `dob (str)`: Date of birth in `YYYYMMDD` format.

        Returns:
        --------
        - `int`: The patient's age.
        - `None`: If the DOB is invalid.
        """
        try:
            birth_date = datetime.strptime(dob, "%Y%m%d")
            today = datetime.today()
            return (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
        except ValueError:
            return None

    def parse(self, message: str) -> tuple[str, dict, list]:
        """
        Parses an HL7 message and extracts relevant data.

        Parameters:
        -----------
        - `message (str)`: The HL7 message string.

        Returns:
        --------
        - `(str | None, dict | None, list | None)`: A tuple containing:
            1. Message type (`ADT^A01`, `ADT^A03`, or `ORU^R01`).
            2. Patient details (for ADT messages) or `None`.
            3. Blood test results (for ORU^R01 messages) or `None`.
        """
        self.reset()  # Reset stored data before parsing a new message

        try:
            segments = message.strip().split("\r")  # Split the message into segments

            for segment in segments:
                fields = segment.split("|")  # Split each segment into fields
                segment_type = fields[0]  # First field represents segment type

                if segment_type == "MSH":
                    self.message_type = (
                        fields[8] if len(fields) > 8 else None
                    )  # We find the type of the message we are currently processing

                elif (
                    segment_type == "PID"
                ):  # If segment type is PID, we will extract patient details
                    self._parse_pid(fields)

                elif (
                    segment_type == "OBR" and self.message_type == "ORU^R01"
                ):  # If the current segment is "OBR",
                    # we will extract the time at which the test was obtained
                    self.test_timestamp = (
                        fields[7]
                        if len(fields) > 7 and fields[7]
                        else datetime.now().isoformat()
                    )

                elif (
                    segment_type == "OBX" and self.message_type == "ORU^R01"
                ):  # If the current segment is "OBX", we will extract the value of the test
                    self._parse_obx(fields)
            output = self._generate_output()
            if output[0] is None:
                logging.error(f"parser.py: [ERROR] Unrecognized message type. Raw HL7 Message: {message}")

            return self._generate_output()

        except (TypeError, IndexError, ValueError) as e:
            logging.error(f"parser.py: Error parsing HL7 message: {e}")

            return None, None, None

    def _parse_pid(self, fields: list) -> None:
        """
        Extracts patient details from a PID segment.

        Parameters:
        -----------
        - `fields (list)`: The fields of the PID segment.
        """
        mrn = fields[3] if len(fields) > 3 and fields[3] else None
        if mrn:
            self.patient_data["mrn"] = int(mrn)  # Store MRN

        if (
            self.message_type == "ADT^A01"
        ):  # Extract additional details only for admissions
            name = fields[5] if len(fields) > 5 else None
            dob = fields[7] if len(fields) > 7 else None
            sex = fields[8] if len(fields) > 8 else None
            age = self.calculate_age(dob) if dob else None
            self.patient_data.update({"name": name, "age": age, "sex": sex})

    def _parse_obx(self, fields: list) -> None:
        """
        Extracts test results from an OBX segment.

        Parameters:
        -----------
        - `fields (list)`: The fields of the OBX segment.
        """
        try:
            test_value = float(fields[5]) if len(fields) > 5 and fields[5] else None
        except (ValueError, IndexError):
            test_value = None  # Handle non-numeric test values

        if "mrn" in self.patient_data:  # Ensure MRN is available before appending test
            self.blood_tests.append(
                {
                    "mrn": self.patient_data["mrn"],
                    "test_value": test_value,
                    "test_time": self.test_timestamp,
                }
            )

    @staticmethod
    def generate_hl7_ack(message: str) -> bytes:
        """
        Generates an HL7 acknowledgment (ACK) message.

        Parameters:
        -----------
        - `message (str)`: The original HL7 message.

        Returns:
        --------
        - `bytes`: The ACK message in HL7 format.
        """
        msg_control_id = "UNKNOWN"
        segments = message.split("\r")

        for segment in segments:
            if segment.startswith("MSH"):
                parts = segment.split("|")
                if len(parts) > 9:
                    msg_control_id = parts[9]

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hl7_ack = f"MSH|^~\\&|||||{timestamp}||ACK^R01|{msg_control_id}|2.5\rMSA|AA|{msg_control_id}\r"

        return START_BLOCK + hl7_ack.encode("utf-8") + END_BLOCK

    def _generate_output(self) -> tuple[str, dict, list]:
        """Generate the parsed output based on message type."""
        if self.message_type in ["ADT^A01", "ADT^A03"]:
            return self.message_type, self.patient_data, None
        if self.message_type == "ORU^R01":
            return self.message_type, None, self.blood_tests
        logging.info(
            f"parser.py: [ERROR] _generate_output() returned None! Message Type: {self.message_type}"
        )

        return None, None, None
