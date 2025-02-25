from prometheus_client import start_http_server, Counter, Gauge

HL7_MESSAGES_RECEIVED = Counter('hl7_messages_received_total', 'Total number of HL7 messages received')
AKI_PAGES_SENT = Counter('aki_pages_sent_total', 'Total number of AKI event pages sent')
AKI_PAGES_FAILED = Counter('aki_pages_failed_total', 'Total number of failed AKI event pages')
PREDICTIONS_MADE = Counter('aki_predictions_total', 'Total number of AKI predictions made')
SYSTEM_UPTIME = Gauge('system_uptime_seconds', 'Time since the system started')