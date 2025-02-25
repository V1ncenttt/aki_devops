import unittest
from datetime import datetime
from src.parser import HL7Parser


class TestHL7Parser(unittest.TestCase):

    def setUp(self):
        """Initialize HL7Parser before each test."""
        self.parser = HL7Parser()

    def test_initialization(self):
        """Test if parser initializes with correct default values."""
        self.assertIsNone(self.parser.message_type)
        self.assertEqual(self.parser.patient_data, {})
        self.assertEqual(self.parser.blood_tests, [])
        self.assertIsNone(self.parser.test_timestamp)

    def test_reset(self):
        """Test if reset correctly clears stored data."""
        self.parser.message_type = "ADT^A01"
        self.parser.patient_data = {"mrn": 123}
        self.parser.blood_tests = [{"test_value": 1.2}]
        self.parser.test_timestamp = "20230101120000"
        self.parser.reset()

        self.assertIsNone(self.parser.message_type)
        self.assertEqual(self.parser.patient_data, {})
        self.assertEqual(self.parser.blood_tests, [])
        self.assertIsNone(self.parser.test_timestamp)

    def test_calculate_age_valid(self):
        """Test age calculation from a valid date of birth."""
        self.assertEqual(
            self.parser.calculate_age("20000101"), datetime.today().year - 2000
        )

    def test_calculate_age_invalid(self):
        """Test age calculation with an invalid date format."""
        self.assertIsNone(self.parser.calculate_age("invalid"))

    def test_parse_adt_a01(self):
        """Test parsing an ADT^A01 (admission) message."""
        message = "MSH|^~\\&|||||20240205120000||ADT^A01|MSG123|2.5\rPID|||123456||Doe^John||19900101|M"
        msg_type, patient_data, _ = self.parser.parse(message)

        self.assertEqual(msg_type, "ADT^A01")
        self.assertEqual(patient_data["mrn"], 123456)
        self.assertEqual(patient_data["name"], "Doe^John")
        self.assertEqual(patient_data["age"], datetime.today().year - 1990)
        self.assertEqual(patient_data["sex"], "M")

    def test_parse_adt_a03(self):
        """Test parsing an ADT^A03 (discharge) message."""
        message = "MSH|^~\\&|||||20240205120000||ADT^A03|MSG124|2.5\rPID|||654321"
        msg_type, patient_data, _ = self.parser.parse(message)

        self.assertEqual(msg_type, "ADT^A03")
        self.assertEqual(patient_data["mrn"], 654321)

    def test_parse_oru_r01(self):
        """Test parsing an ORU^R01 (lab results) message."""
        message = (
            "MSH|^~\\&|SIMULATION|SOUTH RIVERSIDE|||20250209133600||ORU^R01|||2.5\r"
            "PID|1||109318748\r"
            "OBR|1||||||20250209133600\r"
            "OBX|1|SN|CREATININE||165.6468632163597"
        )

        msg_type, _, blood_tests = self.parser.parse(message)
        self.assertEqual(msg_type, "ORU^R01")
        self.assertEqual(len(blood_tests), 1)
        self.assertEqual(blood_tests[0]["mrn"], 109318748)
        self.assertEqual(blood_tests[0]["test_value"], 165.6468632163597)
        self.assertEqual(blood_tests[0]["test_time"], "20250209133600")

    def test_parse_oru_r01_missing_obx(self):
        """Test parsing ORU^R01 without OBX segment."""
        message = (
            "MSH|^~\\&|||||20240205120000||ORU^R01|MSG126|2.5\r"
            "PID|||555666\r"
            "OBR|||20240205115900"
        )
        msg_type, _, blood_tests = self.parser.parse(message)

        self.assertEqual(msg_type, "ORU^R01")
        self.assertEqual(blood_tests, [])

    def test_parse_invalid_message_type(self):
        """Test parsing an HL7 message with an invalid message type."""
        message = "MSH|^~\\&|||||20240205120000||INVALID_TYPE|MSG127|2.5\rPID|||987654"
        msg_type, patient_data, blood_tests = self.parser.parse(message)

        self.assertIsNone(msg_type)
        self.assertIsNone(patient_data)
        self.assertIsNone(blood_tests)

    def test_parse_invalid_numeric_values(self):
        """Test OBX parsing with an invalid numeric value."""
        message = (
            "MSH|^~\\&|||||20240205120000||ORU^R01|MSG128|2.5\r"
            "PID|||222333\r"
            "OBR|||20240205115900\r"
            "OBX|||INVALID"
        )
        msg_type, _, blood_tests = self.parser.parse(message)

        self.assertEqual(msg_type, "ORU^R01")
        self.assertEqual(len(blood_tests), 1)
        self.assertIsNone(blood_tests[0]["test_value"])

    def test_generate_hl7_ack(self):
        """Test HL7 acknowledgment message generation."""
        message = "MSH|^~\\&|||||20240205120000||ADT^A01|MSG129|2.5"
        ack = self.parser.generate_hl7_ack(message).decode("utf-8")

        self.assertTrue(ack.startswith("\x0bMSH|^~\\&|||||"))
        self.assertIn("ACK^R01", ack)
        self.assertIn("MSA|AA|MSG129", ack)
        self.assertTrue(ack.endswith("\x1c\r"))

    def test_generate_hl7_ack_no_msg_id(self):
        """Test HL7 acknowledgment message generation when message ID is missing."""
        message = "MSH|^~\\&|||||20240205120000||ADT^A01||2.5"
        ack = self.parser.generate_hl7_ack(message).decode("utf-8")

        self.assertIn("||ACK^R01||2.5\rMSA|AA|\r\x1c\r", ack)

    def test_singleton(self):
        """Test that HL7Parser is a singleton."""
        parser = HL7Parser()
        self.assertIs(self.parser, parser)


if __name__ == "__main__":
    unittest.main()
