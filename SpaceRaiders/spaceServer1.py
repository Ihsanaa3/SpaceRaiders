import socket
import numpy as np

# Define numpy dtype matching C++ struct memory layout (24 bytes total per Entity)
enityDtype = np.dtype([
    ('position', np.float32, (2,)),
    ('velocity', np.float32, (2,)),
    ('radius',   np.float32),
    ('deltaG',   np.float32)
])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Disable SIO_UDP_CONNRESET on Windows to handle unexpected socket resets gracefully
try:
    sock.ioctl(socket.SIO_UDP_CONNRESET, False)
except AttributeError:
    pass

# Bind Python to Port 8080
sock.bind(("127.0.0.1", 8080))

print("Listening for UDP packets on 127.0.0.1:8080...")

while True:
    data, addr = sock.recvfrom(4096)

    # 1. Read header count (first 4 bytes)
    count = np.frombuffer(data, dtype=np.int32, count=1, offset=0)[0]

    # Check for termination signal
    if count == -1:
        print("Received exit signal from C++. Shutting down...")
        break 

    entities = np.frombuffer(data, dtype=enityDtype, count=count, offset=4).copy()

    allPositions  = entities['position'] 
    allVelocities = entities['velocity'] 
    allDeltaG     = entities['deltaG']

    allVelocities[:, 1] += allDeltaG
    allPositions[:, 1]  += allVelocities[:, 1]
    
    print(f"Received {count} entities from {addr}")

    # --- Process / Update Data Example ---
    send_count = np.int32(count)
    reply_payload = send_count.tobytes() + entities.tobytes()

    # 3. Send back to sender's address (which will now be C++ on port 9090)
    sock.sendto(reply_payload, addr)

sock.close()