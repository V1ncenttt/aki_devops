import socket
import requests
import time

# MLLP Special Characters
MLLP_START_OF_BLOCK = b'\x0b'
MLLP_END_OF_BLOCK = b'\x1c'
MLLP_CARRIAGE_RETURN = b'\x0d'

# Server Connection Details
MLLP_SERVER_HOST = "message_sim"
MLLP_SERVER_PORT = 8440
PAGER_SERVER_URL = "http://message_sim:8441/page"

# Sample ACK HL7 Message (MSA|AA = Acknowledgment Accepted)
def create_ack():
    ack_message = [
        r"MSH|^~\&|ACK_SYSTEM|RECEIVER|||202401291000||ACK|||2.5",  # Use raw string format
        "MSA|AA|MSG001"
    ]

    mllp_ack = MLLP_START_OF_BLOCK + ("\r".join(ack_message) + "\r").encode() + MLLP_END_OF_BLOCK + MLLP_CARRIAGE_RETURN
    return mllp_ack

# Function to handle the connection with MLLP Server
def connect_to_mllp_server():
    while True:
        try:
            print(f"🔄 Connecting to MLLP server at {MLLP_SERVER_HOST}:{MLLP_SERVER_PORT}...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((MLLP_SERVER_HOST, MLLP_SERVER_PORT))
                print("✅ Connected to MLLP server!")

                while True:
                    data = s.recv(1024)  # Receive HL7 Message
                    if not data:
                        print("⚠️ Connection closed by server.")
                        break

                    # Extract HL7 Message (strip MLLP framing)
                    if data.startswith(MLLP_START_OF_BLOCK) and data.endswith(MLLP_END_OF_BLOCK + MLLP_CARRIAGE_RETURN):
                        hl7_message = data[1:-2].decode()
                        print(f"📩 Received HL7 Message:\n{hl7_message}")

                        # Send ACK back to the simulator
                        ack = create_ack()
                        s.sendall(ack)
                        print("✅ Sent ACK (MSA|AA) back to the server.")

                        # Send Pager Notification after processing
                        send_pager_notification()
                    
        except (socket.error, ConnectionRefusedError) as e:
            print(f"❌ Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)  # Wait before retrying

# Function to send a Pager Notification via HTTP
def send_pager_notification():
    payload = "1234,202401291000"  # Example MRN and timestamp
    try:
        response = requests.post(PAGER_SERVER_URL, data=payload, timeout=5)
        if response.status_code == 200:
            print(f"📟 Sent Pager Notification: {payload}")
        else:
            print(f"⚠️ Failed to send Pager Notification. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Pager Notification Error: {e}")

# Start the client
if __name__ == "__main__":
    connect_to_mllp_server()
