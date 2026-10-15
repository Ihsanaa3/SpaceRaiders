import socket
import numpy as np 

def glmdistance2(posx1, posx2, posy1, posy2):
    return (pow(posx1 - posx2, 2) + pow(posy1 - posy2, 2))

# Define numpy dtype matching C++ struct memory layout (24 bytes total per Entity)
entityDtype = np.dtype([
    ('position', np.float32, (2,)),
    ('velocity', np.float32, (2,)),
    ('radius',   np.float32),
    ('deltaG',   np.float32)
])  

packetDtype = np.dtype([
    ('count', np.int32), 
    ('score', np.int32), 
    ('playerMoveKeys', 'S5'), 
    ('player',     entityDtype),
    ('entities',   entityDtype, (50,))
], align=False)

print("NumPy packet size:", packetDtype.itemsize)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Disable SIO_UDP_CONNRESET on Windows to handle unexpected resets gracefully
try:
    sock.ioctl(socket.SIO_UDP_CONNRESET, False)
except (AttributeError, OSError):
    pass

# Bind Python to Port 8080
sock.bind(("127.0.0.1", 8080))
print("Listening for UDP packets on 127.0.0.1:8080...")

dt = 1.0 / 60.0 

while True:
    data, addr = sock.recvfrom(4096) 

    # Guard against invalid or partial datagram sizes
    if len(data) != packetDtype.itemsize:
        print(f"Warning: Received packet of size {len(data)}, expected {packetDtype.itemsize}. Dropping.")
        continue

    # Unpack structured data from buffer
    packetRecieved = np.frombuffer(data, dtype=packetDtype, count=1, offset=0).copy()[0]

    count = packetRecieved['count'] 
    score = packetRecieved['score']
    
    # Check for termination signal
    if count == -1:
        print("Received exit signal from C++. Shutting down...")
        break 

    allEntities     = packetRecieved['entities'] 
    allPositions   = allEntities['position'] 
    allVelocities  = allEntities['velocity'] 
    allRadius      = allEntities['radius']
    allDeltaG      = allEntities['deltaG']    

    player         = packetRecieved['player'] 
    playerPosition = player['position'] 
    playerRadius   = player['radius']

    playerMoveKeys = packetRecieved['playerMoveKeys'].decode('utf-8', errors='ignore').rstrip('\x00') 

    # print(f"count: {count} | Player Move: {playerMoveKeys}")

    # Physics Integration
    allVelocities[:, 1] += allDeltaG * dt
    allPositions[:, 1]  += allVelocities[:, 1] * dt 

    for i in range(count):
        # Reset entity if it falls below screen boundary (-1.0)
        if allPositions[i, 1] < -1.0: 
            allPositions[i, 1] = 1.0 
            allVelocities[i, 1] = 1.0 
            allDeltaG[i] = -1.0 * np.random.uniform(0.0, 1.0 + (score / 1000.0))
        
        # Check collision with player
        dist_sq = glmdistance2(playerPosition[0], allPositions[i, 0], playerPosition[1], allPositions[i, 1])
        if dist_sq < pow(allRadius[i] + playerRadius, 2): 
            allVelocities[:, 1] = 0.0 
            print("Game Over")
            break 

        print(playerPosition)

    # Send updated binary packet back to C++ application
    sock.sendto(packetRecieved.tobytes(), addr) 
    print("data sent") 

sock.close()