from datetime import datetime

# MLLP Delimiters
START_BLOCK = b"\x0b"
END_BLOCK = b"\x1c\r"

class HL7Parser:
    """
   This class is responsible for parsing the incoming messages. Different returns will be produced based on the message type. It can be reused multiple times with different messages.
   """
    
    def __init__(self):
        """Initialize the parser with default values."""
        self.reset()
    
    def reset(self):
        """Reset the parser's stored data to ensure clean parsing for a new message."""
        self.message_type = None
        self.patient_data = {}
        self.blood_tests = []
        self.test_timestamp = None
    
    def calculate_age(self, dob):
        """Calculate age from date of birth. This function will be used to return the patient's age instead of their date of birth, when being admitted to a hospital."""
        try:
            birth_date = datetime.strptime(dob, "%Y%m%d")
            today = datetime.today()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            return None
    
    def parse(self, message):
        """Parse the given HL7 message."""
        self.reset()  # Reset stored data before parsing a new message
        
        try:
            segments = message.strip().split("\r")  # Split the message into segments
            
            for segment in segments:
                fields = segment.split("|")  # Split each segment into fields
                segment_type = fields[0]  # First field represents segment type
                
                if segment_type == "MSH": 
                    self.message_type = fields[8] if len(fields) > 8 else None # We find the type of the message we are currently processing

                elif segment_type == "PID": # If segment type is PID, we will extract patient details
                    self._parse_pid(fields)

                elif segment_type == "OBR" and self.message_type == "ORU^R01": # If the current segment is "OBR", we will extract the time at which the test was obtained
                    self.test_timestamp = fields[6] if len(fields) > 6 and fields[6] else datetime.now().isoformat()
                    
                elif segment_type == "OBX" and self.message_type == "ORU^R01": # If the current segment is "OBX", we will extract the value of the test
                    self._parse_obx(fields)
            output = self._generate_output()
            if output[0] is None:
                print(f"[ERROR] Unrecognized message type. Raw HL7 Message: {message}")  
            
            return self._generate_output()
        
        except Exception as e:
            print(f"Error parsing HL7 message: {e}")
            
            return None, None, None

    def _parse_pid(self, fields):
        """Extract patient information from the PID segment."""
        mrn = fields[3] if len(fields) > 3 and fields[3] else None
        if mrn:
            self.patient_data["mrn"] = int(mrn)  # Store MRN
        
        if self.message_type == "ADT^A01":  # Extract additional details only for admissions
            name = fields[5] if len(fields) > 5 else None
            dob = fields[7] if len(fields) > 7 else None
            gender = fields[8] if len(fields) > 8 else None
            age = self.calculate_age(dob) if dob else None
            self.patient_data.update({"name": name, "age": age, "gender": gender})
    
    def _parse_obx(self, fields):
        """Extract test results from the OBX segment."""
        try:
            test_value = float(fields[5]) if len(fields) > 5 and fields[5] else None
        except (ValueError, IndexError):
            test_value = None  # Handle non-numeric test values
        
        if "mrn" in self.patient_data:  # Ensure MRN is available before appending test
            self.blood_tests.append({
                "mrn": self.patient_data["mrn"],
                "test_value": test_value,
                "test_time": self.test_timestamp
            })
    
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

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        hl7_ack = f"MSH|^~\\&|||||{timestamp}||ACK^R01|{msg_control_id}|2.5\rMSA|AA|{msg_control_id}\r"

        return START_BLOCK + hl7_ack.encode("utf-8") + END_BLOCK
    
    def _generate_output(self): 
        """Generate the parsed output based on message type."""
        if self.message_type in ["ADT^A01", "ADT^A03"]:
            return self.message_type, self.patient_data, None
        elif self.message_type == "ORU^R01":
            return self.message_type, None, self.blood_tests
        print(f"[ERROR] _generate_output() returned None! Message Type: {self.message_type}")  

        return None, None, None


