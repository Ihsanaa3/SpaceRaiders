import socket
import numpy as np
import torch
import torch.nn as nn
import os
import gc
import time 

gc.disable()

# ==========================================
# 1. Dueling DQN Model Architecture (Matches Training)
# ==========================================
class DuelingDQN(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DuelingDQN, self).__init__()
        self.feature_stream = nn.Sequential(
            nn.Linear(state_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU()
        )
        
        self.value_stream = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )
        
        self.advantage_stream = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim)
        )

    def forward(self, x):
        features = self.feature_stream(x)
        values = self.value_stream(features)
        advantages = self.advantage_stream(features)
        q_values = values + (advantages - advantages.mean(dim=-1, keepdim=True))
        return q_values

# ==========================================
# 2. Packet & Entity Data Types
# ==========================================

expectedEntitySize = 50

entityDtype = np.dtype([
    ('position', np.float32, (2,)),
    ('velocity', np.float32, (2,)),
    ('radius',   np.float32),
    ('deltaG',   np.float32)
]) 

packetDtype = np.dtype([
    ('count', np.int32), 
    ('score', np.int32), 
    ('player',    entityDtype),
    ('entities',  entityDtype, (expectedEntitySize,))
], align=False)

print("NumPy packet size:", packetDtype.itemsize)

# Setup UDP Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    sock.ioctl(socket.SIO_UDP_CONNRESET, False)  # type: ignore
except (AttributeError, OSError):
    pass

sock.bind(("127.0.0.1", 8080))
print("listening on 127.0.0.1:8080...")

# ==========================================
# 3. Load Trained PyTorch Model
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Must match training max_balls = 50 (state_dim = 202)
EXPECTED_BALLS = 50 
state_dim = 2 + (EXPECTED_BALLS * 2) + (EXPECTED_BALLS * 2)  # player (2) + pos (100) + vel (100) = 202
action_dim = 16  # 16 discrete bitmask actions

model_path = "SpaceRaiders/spefnnt_anticamping_dqn.pth"

policy_net = DuelingDQN(state_dim, action_dim).to(device)
if os.path.exists(model_path):
    policy_net.load_state_dict(torch.load(model_path, map_location=device))
    print(f"Successfully loaded trained model from: {model_path}")
else:
    print(f"Warning: Model file not found at {model_path}! AI will take random/uninitialized actions.")

policy_net.eval()

# Physics / Game Loop Variables
GAMEOVER = False
dt = 1.0 / 40.0 
playerSpeed = 0.9

playerServerPosition = np.array([0.0, 0.0], dtype=np.float32) 
allServerPositions = np.zeros((expectedEntitySize, 2), dtype=np.float32) 
allServerVelocities = np.zeros((expectedEntitySize, 2), dtype=np.float32)

for i in range(expectedEntitySize):
    allServerPositions[i, 0] = np.random.uniform(-1.0, 1.0) 
    allServerPositions[i, 1] = 1.0   

# ==========================================
# 4. Main UDP & AI Execution Loop
# ==========================================
while True: 
    data, addr = sock.recvfrom(4096) 

    if len(data) != packetDtype.itemsize:
        continue

    packetReceived = np.frombuffer(data, dtype=packetDtype, count=1, offset=0).copy()[0]

    count = packetReceived['count'] 
    score = packetReceived['score'] 
    
    if count == -1: 
        print(count)
        print("Received exit signal from C++. Shutting down...") 
        break 

    allEntities  = packetReceived['entities'] 
    allRadius    = allEntities['radius']
    allDeltaG    = allEntities['deltaG'] 
    playerRadius = packetReceived['player']['radius']

    if count == -2: 
        print(count)
        print("Restarting game state...") 
        GAMEOVER = False 
        bigballs = expectedEntitySize

        for i in range(bigballs):
            allServerPositions[i, 0] = np.random.uniform(-1.0, 1.0) 
            allServerPositions[i, 1] = 1.0 
            allServerVelocities[i, 1] = 0.0 
            allDeltaG[i] = -np.random.uniform(0.4, 0.8) 

        playerServerPosition = np.array([0.0, 0.0], dtype=np.float32) 

        packetReceived['count'] = bigballs
        packetReceived['score'] = 0
        packetReceived['entities']["deltaG"] = allDeltaG

        sock.sendto(packetReceived.tobytes(), addr) 
        gc.collect()
        continue 

    if count == -3:
        print(count)
        print(score)
        allServerVelocities[:, 1] = 0.0 
        GAMEOVER = True 
        print("Game Over Collision Detected") 

    if GAMEOVER:
        continue

    # --- 5. BUILD STATE VECTOR FOR AI ---
    state_vector = np.concatenate([
        playerServerPosition,
        allServerPositions.flatten(),
        allServerVelocities.flatten()
    ]).astype(np.float32) 

    # --- 6. AI PREDICTION (DUELING DQN FORWARD PASS) ---
    with torch.no_grad():
        state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(device)
        q_values = policy_net(state_tensor)
        action = q_values.argmax().item()  # Choose best action (0-15)

    # Convert discrete action (0-15 bitmask) into movement keys string [Right, Left, Up, Down]
    r = '1' if (action & 1) else '0'
    l = '1' if (action & 2) else '0'
    u = '1' if (action & 4) else '0'
    d = '1' if (action & 8) else '0'
    playerMoveKeys = f"{r}{l}{u}{d}"

    # --- 7. PLAYER POSITION & PHYSICS LOGIC ---
    if len(playerMoveKeys) >= 4:
        if playerMoveKeys[0] == '1': playerServerPosition[0] += playerSpeed * dt
        if playerMoveKeys[1] == '1': playerServerPosition[0] -= playerSpeed * dt
        if playerMoveKeys[2] == '1': playerServerPosition[1] += playerSpeed * dt
        if playerMoveKeys[3] == '1': playerServerPosition[1] -= playerSpeed * dt

    # Boundary clamping
    boundaryLimit = 1.0 - playerRadius
    playerServerPosition[0] = np.clip(playerServerPosition[0], -boundaryLimit, boundaryLimit)
    playerServerPosition[1] = np.clip(playerServerPosition[1], -boundaryLimit, boundaryLimit)

    # Physics integration
    allServerVelocities[:, 1] += allDeltaG * dt
    allServerPositions[:, 1]  += allServerVelocities[:, 1] * dt 

    for i in range(count):
        if allServerPositions[i, 1] < -1.0: 
            allServerPositions[i, 1] = 1.0 
            allServerVelocities[i, 1] = 0.0 
            allDeltaG[i] = -np.random.uniform(0.0, 1.0 + (score / 1000.0))
            allServerPositions[i, 0] = np.random.uniform(-1.0, 1.0) 
                    # Collision check with player
        dist_sq = (pow(playerServerPosition[0] - allServerPositions[i, 0], 2) + 
                    pow(playerServerPosition[1] - allServerPositions[i, 1], 2))
        
        if dist_sq < pow(allRadius[i] + playerRadius, 2): 
            print(score)
            allServerVelocities[:, 1] = 0.0 
            GAMEOVER = True 
            print("Game Over Collision Detected ") 

        
    # Update packet state back to send to C++ OpenGL renderer
    packetReceived['player']['position'] = playerServerPosition
    packetReceived['entities']['position'] = allServerPositions
    packetReceived['entities']['velocity'] = allServerVelocities

    sock.sendto(packetReceived.tobytes(), addr)

gc.collect()
sock.close()