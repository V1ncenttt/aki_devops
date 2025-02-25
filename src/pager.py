"""
Pager Alert Module
==================
This module provides the `Pager` class, which is responsible for sending pager alerts asynchronously 
in case of medical emergencies. It communicates with a remote pager system via HTTP requests.

Authors:
--------
- Vincent Lefeuve (vincent.lefeuve24@imperial.ac.uk)

Classes:
--------
- `Pager`: Handles sending alerts to an external pager system.

Usage:
------
Example:
    pager = Pager("127.0.0.1:5000")
    pager.run(12345, "2025-02-07T12:30:00")

"""

import logging
import requests
import time
from src.metrics import AKI_PAGES_SENT, AKI_PAGES_FAILED

class Pager:
    """
    Pager System for Emergency Alerts
    ==================================
    This class sends alerts to an external pager system in case of medical emergencies.
    It retries sending the alert up to three times in case of failure.

    Attributes:
    -----------
    - `pager_url (str)`: The URL of the pager system to which alerts are sent.
    """
    def __init__(self, pager_address):
        """
        Initializes the Pager with the given address.
        
        Args:
            pager_address (str): The IP and port of the pager system in the format 'host:port'.
        """
        pager_host = pager_address.split(":")[0]
        pager_port = pager_address.split(":")[1]
        self.pager_url = f"http://{pager_host}:{pager_port}/page"   
        pass

    def send_pager_alert(self, mrn, timestamp):
        """
        Sends a pager alert asynchronously.
        
        Args:
            mrn (int): Patient's medical record number.
            timestamp (str): Time of the alert in ISO format.
        
        Retries up to three times in case of failure.
        """
        timestamp = timestamp.replace("-", "").replace(" ", "").replace(":", "").replace('T', '').split('.')[0]

        logging.info(f"[*] Sending pager alert for Patient {mrn} at {timestamp}...")

        content = f"{mrn},{timestamp}"

        for _ in range(3):  # Retry 3 times if there is a failure
            try:
                response = requests.post(self.pager_url, data=content, timeout=5)
                AKI_PAGES_SENT.inc()
                if response.status_code != 200:
                    AKI_PAGES_FAILED.inc()
                response.raise_for_status()
                return
            except requests.RequestException as e:
                logging.warning(f"[ALERT FAILED] Retrying... {e}")
                time.sleep(1)  # Wait before retrying
        return
