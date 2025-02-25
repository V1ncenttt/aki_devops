from prometheus_client import start_http_server, Counter, Gauge

HL7_MESSAGES_RECEIVED = Counter('hl7_messages_received_total', 'Total number of HL7 messages received')
INCORRECT_MESSAGES_RECEIVED = Counter('inccorect_messages_received_total', 'Total number of incorrectly formed HL7 messages received')
BLOOD_TEST_RESULTS_RECEIVED = Counter('blood_test_results_received_total', 'Total number of HL7 messages received containing blood test results')
AKI_PAGES_SENT = Counter('aki_pages_sent_total', 'Total number of AKI event pages sent')
AKI_PAGES_FAILED = Counter('aki_pages_failed_total', 'Total number of failed AKI event pages')
PREDICTIONS_MADE = Counter('aki_predictions_total', 'Total number of AKI predictions made')
POSITIVE_PREDICTIONS_MADE = Counter('aki_positive_predictions_total', 'Total number of positive AKI predictions made')
MLLP_RECONNECTIONS = Counter('mllp_reconnections_total', 'Total number of mllp reconnection attempts to the socket')
SYSTEM_UPTIME = Gauge('system_uptime_seconds', 'Time since the system started')