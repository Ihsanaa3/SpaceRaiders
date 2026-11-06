import numpy as np
import time 

def glmdistance2(posx1, posx2, posy1, posy2):
    return (pow(posx1 - posx2, 2) + pow(posy1 - posy2, 2))


class SPEFNNT:
    '''Space Raider Engine For Neural Network Training''' 

    def __init__(self, noBalls=50):
        
        ### FB is Falling Ball

        self.noBalls = noBalls 
        self.FB_radius = 0.06 
        self.player_radius = 0.04 
        self.player_speed = 1.0 

        self.score = 0
        self.GAMEOVER = False 

        self.FB_position     =  np.ones((noBalls, 2), dtype=np.float32) 
        self.FB_velocity     = np.zeros((noBalls, 2), dtype=np.float32)  
        self.FB_acceleration = np.zeros((noBalls,), dtype=np.float32) 
        self.player_position = np.array([0.0, 0.0], dtype=np.float32) 

    def NN1D(self):
        '''Returns a 1D array for the neural network that consists of the player pos, FB pos and FB vel'''
        D1Array = np.concatenate([self.player_position, self.FB_position.flatten(), self.FB_velocity.flatten()])
        return D1Array
    
    def resetFB(self):
        self.score = 0 
        self.GAMEOVER = False
        self.FB_position[:, 1] = 1.0 
        self.player_position = np.zeros((2,), dtype=np.float32)

        for i in range(self.noBalls):
            self.FB_position[i, 0] = np.random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius) 
            self.FB_position[i, 1] = 1.0  
            self.FB_velocity[i, 1] = 0.0 
            self.FB_acceleration[i] = np.random.uniform(high= 1 + (self.score/1000)) 

        return self.NN1D() 

    def NextFrame(self, action):
        '''Takes in a 2D array of vx, vy and then moves the player accordingly''' 

        if self.GAMEOVER:
            # returns the observation, reward and then gameover
            return self.NN1D(), 0.0, True 

        dt = 1/40 
        reward = 1 
        self.score += 1 

        NN_Move_vec2 = np.array([0.0, 0.0], dtype=np.float32) 

        if action & 1: NN_Move_vec2[0] += 1.0  # Right bit is 1 (0001)
        if action & 2: NN_Move_vec2[0] -= 1.0  # Left bit is 1  (0010)
        if action & 4: NN_Move_vec2[1] += 1.0  # Up bit is 1    (0100)
        if action & 8: NN_Move_vec2[1] -= 1.0  # Down bit is 1  (1000)         

        self.player_position += NN_Move_vec2 *self.player_speed * dt 

        self.player_position = np.clip(self.player_position, -1.0 + self.player_radius, 1.0 - self.player_radius) 

        self.FB_velocity[:, 1] -= self.FB_acceleration * dt
        self.FB_position[:, 1] += self.FB_velocity[:, 1] * dt 

        for i in range(self.noBalls):
            if self.FB_position[i, 1] < -1.0:
                self.FB_position[i, 1] = 1.0
                self.FB_position[i, 0] = np.random.uniform(-1.0 + self.FB_radius, 1.0 - self.FB_radius)  
                self.FB_velocity[i, 1] = 0.0  

            dist = glmdistance2(
                self.FB_position[i, 0], self.player_position[0], 
                self.FB_position[i, 1], self.player_position[1]
            ) 
            twoR2 = pow(self.FB_radius + self.player_radius, 2)  

            if dist < twoR2:
                self.GAMEOVER = True 
                reward = -100 
                break 

        return self.NN1D(), reward, self.GAMEOVER 


env = SPEFNNT() 
obs = env.resetFB()           

for _ in range(10000):
    action = np.random.randint(0, 16) # Placeholder for PyTorch model action output
    obs, reward, done = env.NextFrame(action)
    if reward == -100:
        print(reward)
    if done: 
        obs = env.resetFB() 
