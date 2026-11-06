import numpy as np
import math 
import time 

def glmdistance2(posx1, posx2, posy1, posy2):
    return (pow(posx1 - posx2, 2) + pow(posy1 - posy2, 2))


class ball:
    radius = 0.06 
    def __init__(self):
        self.pos = np.array([0.0, 0.0]) 
        self.vel = np.array([0.0, 0.0])
        self.acc = 0.0  

noballs = 50

position = np.ones((noballs, 2), dtype=np.float32) 
velocity = np.zeros((noballs, 2), dtype=np.float32) 
acceleration = np.zeros((noballs), dtype=np.float32) 

player = ball() 

for i in range(noballs):
    ranx = np.random.uniform(-1.0, 1.0) 
    ranacc = np.random.uniform(0.0, 1.0) 
    position[i, 0] = ranx 
    acceleration[i] = ranacc 


dt = 1 / 40 
GAMEOVER = False 
score = 0 
playerSpeed = 0.9
prevTime = time.perf_counter() 

while True:
    crntTime = time.perf_counter() 

    if crntTime - prevTime >= dt and GAMEOVER != True:
        prevTime = crntTime 
        score += 1 

        velocity[:, 1] -= acceleration * dt 
        position[:, 1] += velocity[:, 1] * dt 

        for i in range(noballs):
            if position[i, 1] < -1.0:
                position[i, 1] = 1.0 
                velocity[i, 1] = 0.0 
                acceleration[i] = np.random.uniform(0.0, 1.0 + (score / 1000.0))
                position[i, 0] = np.random.uniform(-1.0, 1.0) 

            if glmdistance2(position[i, 0], player.pos[0], position[i, 1], player.pos[1]) < pow(2 * player.radius, 2): 
                velocity[:, 1] = 0.0
                GAMEOVER = True 
                score = 0


    if GAMEOVER == True:
        print("Restarting game state...") 
        GAMEOVER = False 

        for i in range(noballs):
            position[i, 0] = np.random.uniform(-1.0, 1.0) 
            position[i, 1] = 1.0 
            velocity[i, 1] = 0.0 
            acceleration[i] = -1.0 * np.random.uniform(0.0, 1.0 + (score / 1000.0))

        continue

    if GAMEOVER == False:
        print(position) 
    else:
        print("GAME OVER ")