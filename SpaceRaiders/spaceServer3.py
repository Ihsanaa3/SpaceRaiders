import socket
import numpy as np 
import time 
import os
import gc                  # Garbage collection 

gc.disable() 

def glmdistance2(posx1, posx2, posy1, posy2):
    return (pow(posx1 - posx2, 2) + pow(posy1 - posy2, 2))

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
    ('player',    entityDtype),
    ('entities',  entityDtype, (50,))
], align=False)

print("NumPy packet size:", packetDtype.itemsize)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    sock.ioctl(socket.SIO_UDP_CONNRESET, False)
except (AttributeError, OSError):
    pass

sock.bind(("127.0.0.1", 8080))
print("Listening for UDP packets on 127.0.0.1:8080...")

expectedEntitySize = 50

GAMEOVER = False
dt = 1.0 / 40.0 
playerSpeed = 0.9

playerServerPosition = np.array([0.0, 0.0], dtype=np.float32) 
allServerPositions = np.zeros((expectedEntitySize, 2), dtype=np.float32) 
for i in range(expectedEntitySize):
    allServerPositions[i, 0] = np.random.uniform(-1.0, 1.0) 
    allServerPositions[i, 1] = 1.0 


allServerVelocities = np.zeros((expectedEntitySize, 2), dtype=np.float32)

while True:
    # loop_start_time = time.perf_counter()
    
    data, addr = sock.recvfrom(4096) 

    if len(data) != packetDtype.itemsize:
        continue

    packetReceived = np.frombuffer(data, dtype=packetDtype, count=1, offset=0).copy()[0]

    count = packetReceived['count'] 
    score = packetReceived['score'] 

    # print(f"Score: {score}") 
    
    if count == -1:
        print("Received exit signal from C++. Shutting down...") 

        break 

    allEntities   = packetReceived['entities'] 
    # allServerPositions  = allEntities['position'] 
    # allServerVelocities = allEntities['velocity'] 
    allRadius     = allEntities['radius']
    allDeltaG     = allEntities['deltaG']    

    if count == -2: 
        print("Restarting game state...") 
        GAMEOVER = False 
        bigballs = expectedEntitySize

        for i in range(bigballs):
            allServerPositions[i, 0] = np.random.uniform(-1.0, 1.0) 
            allServerPositions[i, 1] = 1.0 
            allServerVelocities[i, 1] = 0.0 
            allDeltaG[i] = -1.0 * np.random.uniform(0.0, 1.0 + (score / 1000.0))

        packetReceived['count'] = bigballs
        packetReceived['score'] = 0
        packetReceived['player']['position'] = [0.0, 0.0]
        packetReceived['entities']['position'] = allServerPositions
        packetReceived['entities']['velocity'] = allServerVelocities 
        packetReceived['entities']["deltaG"] = allDeltaG

        sock.sendto(packetReceived.tobytes(), addr)  

        gc.collect(); 

        continue

    if GAMEOVER == True:
        continue

    player        = packetReceived['player'] 
    playerPosition = player['position'] 
    playerRadius  = player['radius']

    playerMoveKeys = packetReceived['playerMoveKeys'].decode('utf-8', errors='ignore').rstrip('\x00') 

    # --- 1. PLAYER POSITION & INPUT LOGIC ---
    if len(playerMoveKeys) >= 4:
        # directions format: [Right, Left, Up, Down]
        if playerMoveKeys[0] == '1': playerServerPosition[0] += playerSpeed * dt
        if playerMoveKeys[1] == '1': playerServerPosition[0] -= playerSpeed * dt
        if playerMoveKeys[2] == '1': playerServerPosition[1] += playerSpeed * dt
        if playerMoveKeys[3] == '1': playerServerPosition[1] -= playerSpeed * dt

    # Player boundary clamping
    boundaryLimit = 1.0 - playerRadius
    playerServerPosition[0] = np.clip(playerServerPosition[0], -boundaryLimit, boundaryLimit)
    playerServerPosition[1] = np.clip(playerServerPosition[1], -boundaryLimit, boundaryLimit)

    # --- 2. PHYSICS INTEGRATION ---
    allServerVelocities[:, 1] += allDeltaG * dt
    allServerPositions[:, 1]  += allServerVelocities[:, 1] * dt 

    score += 1  # Increment score over time

    for i in range(count):
        # Reset entity if it falls below screen boundary (-1.0)
        if allServerPositions[i, 1] < -1.0: 
            allServerPositions[i, 1] = 1.0 
            allServerVelocities[i, 1] = 0.0 
            allDeltaG[i] = -1.0 * np.random.uniform(0.0, 1.0 + (score / 1000.0))
            allServerPositions[i, 0] = np.random.uniform(-1.0, 1.0)
        
        # Check collision with player
        dist_sq = glmdistance2(playerServerPosition[0], allServerPositions[i, 0], playerServerPosition[1], allServerPositions[i, 1])
        
        if dist_sq < pow(allRadius[i] + playerRadius, 2): 
            allServerVelocities[:, 1] = 0.0 
            GAMEOVER = True 
            # --- High Score File Saving Logic ---
            highScorePath = "Highestscore.txt"
            currentHighScore = 0
            if os.path.exists(highScorePath):
                try:
                    with open(highScorePath, "r") as f:
                        content = f.read().strip()
                        if content:
                            currentHighScore = int(content)
                except Exception:
                    pass

            if score > currentHighScore:
                try:
                    with open(highScorePath, "w") as f:
                        f.write(str(score))
                    print(f"New High Score Saved!: {score}")
                except Exception:
                    pass
            else:
                print(f"{score} does not beat {currentHighScore}...")

            print("Game Over Collision Detected")

    # Update packet state back to send
    packetReceived['score'] = score
    packetReceived['player']['position'] = playerServerPosition
    packetReceived['entities']['position'] = allServerPositions
    packetReceived['entities']['velocity'] = allServerVelocities

    # Send updated binary packet back to C++ application
    sock.sendto(packetReceived.tobytes(), addr) 

    # loop_end_time = time.perf_counter()
    # loop_duration = loop_end_time - loop_start_time

    # print(f"Python loop took: {loop_duration * 1000:.4f} ms")

gc.collect()

sock.close()