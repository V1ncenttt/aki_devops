import logging
import requests

class Pager:
    def __init__(self, pager_address):
        pager_host = pager_address.split(":")[0]
        pager_port = pager_address.split(":")[1]
        self.pager_url = f"http://{pager_host}:{pager_port}/page"   
        pass

    def send_pager_alert(self, mrn, timestamp):
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
                time.sleep(1)  # Wait before retrying