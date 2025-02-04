import socket
import datetime
import queue

# MLLP Delimiters
START_BLOCK = b'\x0b'  # VT (Vertical Tab)
END_BLOCK = b'\x1c\r'  # FS (File Separator) + Carriage Return

# Connection details
HOST = "127.0.0.1"  # Connect to the simulator
PORT = 8440         # Port where simulator listens

def generate_hl7_ack(message):
    """Generate a valid HL7 ACK message with MSA segment."""
    # Extract message control ID (from MSH segment)
    msg_control_id = "UNKNOWN"
    lines = message.split("\r")  # HL7 uses \r, not \n

    for line in lines:
        if line.startswith("MSH"):
            parts = line.split("|")
            if len(parts) > 9:
                msg_control_id = parts[9]  # HL7 Message Control ID

    # Generate timestamp
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")

    # Proper HL7 ACK message with correct format
    hl7_ack = f"MSH|^~\\&|||||{timestamp}||ACK^R01|{msg_control_id}|2.5\r" \
              f"MSA|AA|{msg_control_id}\r"

    # Wrap ACK in MLLP protocol
    return START_BLOCK + hl7_ack.encode("utf-8") + END_BLOCK

def connect_to_mllp_server():
    """Connect to the MLLP simulator and process HL7 messages."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print(f"[+] Connected to MLLP simulator on {HOST}:{PORT}")

        buffer = b""  # Buffer to store received data
        message_queue = queue.Queue()  # Queue to store HL7 messages

        while True:
            try:
                data = client.recv(1024)
                if not data:
                    print("[-] Connection closed by server")
                    break
                
                buffer += data

                # Process complete HL7 MLLP messages
                while START_BLOCK in buffer and END_BLOCK in buffer:
                    start_index = buffer.index(START_BLOCK) + 1
                    end_index = buffer.index(END_BLOCK)
                    hl7_message = buffer[start_index:end_index].decode("utf-8").strip()
                    message_queue.put(hl7_message)
                    print(f"[HL7 MESSAGE]:\n{hl7_message}")

                    # Remove processed message from buffer
                    buffer = buffer[end_index + len(END_BLOCK):]

                    # Generate and send ACK
                    ack_message = generate_hl7_ack(hl7_message)
                    client.sendall(ack_message)
                    print(f"[ACK SENT]:\n{ack_message.decode('utf-8')}")

            except ConnectionResetError:
                print("[-] Connection lost")
                break
        return message_queue

if __name__ == "__main__":
    queue = connect_to_mllp_server()
    #while not queue.empty():
        #print(queue.get())