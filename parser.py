from datetime import datetime

def calculate_age(dob):
    """Calculate age from date of birth. This function will be used within parser to return patient's age instead of date of birth"""
    try:
        birth_date = datetime.strptime(dob, "%Y%m%d")
        today = datetime.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        return None  

def parse_message(message):
    """
    This function parses the message given to it. Different outputs will be produced depending on the message type.
    If the message provided is admitted patient message, the function will return patient's name, age, gender, and MRN.
    If a patient is getting discharged, the function will return the patient's MRN.
    If the message provided is a new test result, the function will return the MRN, test result, and time of the test.
    Besides these message specific returns, the function will also always return the message type.
    """
    try:
        # Firstly we split the message on "\r" values
        segments = message.strip().split("\r")

        # Defining variables for storing the data from the messsage
        message_type = None
        patient_data = {}  
        blood_tests = []
        test_timestamp = None 

        # We also split on "|", which separate fields with values in the messages
        for segment in segments:
            fields = segment.split("|")
            segment_type = fields[0] # We find the type of the segment, which is stored in the first field

            if segment_type == "MSH":
                message_type = fields[8] if len(fields) > 8 else None # We find the type of the message we are currently processing
            
            elif segment_type == "PID":  # If segment type is PID, we will extract patient details
                mrn = fields[3] if len(fields) > 3 else None
                if mrn:
                    patient_data["mrn"] = int(mrn) # Storing the MRN
                
                if message_type == "ADT^A01":  # If a patient is getting addmitted, we will also extract their name, DOB, gender and age
                    name = fields[5] if len(fields) > 5 else None
                    dob = fields[7] if len(fields) > 7 else None
                    gender = fields[8] if len(fields) > 8 else None
                    age = calculate_age(dob) if dob else None
                    patient_data.update({"name": name, "age": age, "gender": gender})

            # If the current segment is "OBR", we will extract the time at which the test was obtained
            elif segment_type == "OBR" and message_type == "ORU^R01":
                test_timestamp = fields[6] if len(fields) > 6 and fields[6] else datetime.now().isoformat()

            # If the current segment is "OBX", we will extract the value of the test
            elif segment_type == "OBX" and message_type == "ORU^R01":
                test_value = float(fields[5]) if len(fields) > 5 and fields[5] else None
                blood_tests.append({
                    "mrn": patient_data.get("mrn"), 
                    "test_value": test_value,
                    "test_time": test_timestamp  
                }) 

        # Returns based on the message type
        if message_type == "ADT^A01":
            return message_type, patient_data, None
        elif message_type == "ADT^A03":
            return message_type, patient_data, None
        elif message_type == "ORU^R01":
            return message_type, None, blood_tests
        return None, None, None

    except Exception as e:
        print(f"Error parsing HL7 message: {e}")
        return None, None, None
